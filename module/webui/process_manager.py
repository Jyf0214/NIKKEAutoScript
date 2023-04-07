import queue
import threading
from multiprocessing import Process
from typing import List, Dict

from filelock import FileLock
from rich.console import ConsoleRenderable

from main import NikkeAutoScript
from module.config.utils import filepath_config
from module.logger import set_file_logger, set_func_logger, logger
from module.webui.setting import State


class ProcessManager:
    # 当前进程列表
    _processes: Dict[str, "ProcessManager"] = {}

    def __init__(self, config_name: str = "nkas") -> None:
        # 配置名称
        self.config_name = config_name
        # 进程共享渲染队列
        self._renderable_queue: queue.Queue[ConsoleRenderable] = State.manager.Queue()
        # 渲染后队列
        self.renderables: List[ConsoleRenderable] = []
        # 最大渲染数
        self.renderables_max_length = 400
        self.renderables_reduce_length = 80
        # 进程实例
        self._process: Process = None
        # 日志队列处理线程
        self.thd_log_queue_handler: threading.Thread = None

    @classmethod
    def get_manager(cls, config_name: str) -> "ProcessManager":
        if config_name not in cls._processes:
            logger.info(f'create ProcessManager: {config_name}')
            cls._processes[config_name] = ProcessManager(config_name)
        return cls._processes[config_name]

    @staticmethod
    def run_process(
            config_name, func: str, q: queue.Queue, e: threading.Event = None
    ) -> None:
        set_func_logger(func=q.put)
        '''
            从logger.py 93行
            重写Rich的RichHandler类
            将渲染后的log通过Queue().put(item)存入State.manager.Queue()中，进程共享渲染队列
        '''

        set_file_logger(name=config_name)
        NikkeAutoScript(config_name=config_name).loop()

    def start(self, func, ev: threading.Event = None) -> None:
        if not self.alive:
            '''
             run_process(config_name, func: str, q: queue.Queue, e: threading.Event = None)
                q: State.manager.Queue() 进程共享渲染队列
                e: 停止事件
                func: 创建进程执行的方法，在Alas中，默认为执行
                AzurLaneAutoScript(config_name='alas').loop()
            '''
            self._process = Process(
                target=ProcessManager.run_process,
                args=(
                    self.config_name,
                    func,
                    self._renderable_queue,
                    ev,
                ),
            )
            self._process.start()
            self.start_log_queue_handler()

    def start_log_queue_handler(self):
        if self.thd_log_queue_handler and self.thd_log_queue_handler.is_alive():
            return
        '''
           创建跟当前进程关联的日志处理线程，并运行
        '''
        self.thd_log_queue_handler = threading.Thread(
            target=self._thread_log_queue_handler
        )
        self.thd_log_queue_handler.start()

    def _thread_log_queue_handler(self) -> None:
        while self.alive:
            try:
                '''
                    从logger.py 93行
                    重写Rich的RichHandler类
                    将渲染后的log通过Queue().put(item)存入State.manager.Queue()中，进程共享渲染队列
                '''
                log = self._renderable_queue.get(timeout=1)
            except queue.Empty:
                continue
            '''
                从进程共享渲染队列获取渲染后的日志
                日志队列大于400时，截取第80个到最后一位
                然后日志会通过在base.py中创建的WebIOTaskHandler，继承TaskHandler类的子任务处理器
                在app.py 101行中，添加到子任务处理器的log.put_log(ProcessManager)方法
                put_log参数为ProcessManager.get_manager()创建的ProcessManager实例
                
                log = RichLog("log")
                self.task_handler.add(log.put_log(self.nkas), delay=0.25, pending_delete=True)
                
                TaskHandler会在后台不断执行put_log方法
                然后日志会通过在webui/widgets.py中的put_log方法渲染到web界面
            '''
            self.renderables.append(log)
            if len(self.renderables) > self.renderables_max_length:
                self.renderables = self.renderables[self.renderables_reduce_length:]
        logger.info("End of log queue handler loop")

    @property
    def alive(self) -> bool:
        if self._process is not None:
            return self._process.is_alive()
        else:
            return False

    def stop(self) -> None:
        lock = FileLock(f"{filepath_config(self.config_name)}.lock")
        with lock:
            if self.alive:
                self._process.kill()
                self.renderables.append(
                    f"[{self.config_name}] exited. Reason: Manual stop\n"
                )
            if self.thd_log_queue_handler is not None:
                self.thd_log_queue_handler.join(timeout=1)
                if self.thd_log_queue_handler.is_alive():
                    logger.warning(
                        "Log queue handler thread does not stop within 1 seconds"
                    )
        logger.info(f"[{self.config_name}] exited")