import functools
import time

# def Timeout(origin):
#     @functools.wraps(origin)
#     def prefix(*args, **kwargs):
#         timeout = Timer(10).start()
#         confirm_timer = Timer(0.5, count=2).start()
#         click_timer = Timer(0.3).reset()
#         res = None
#         while 1:
#             if click_timer.reached():
#                 res = origin(*args, **kwargs)
#                 click_timer.reset()
#                 confirm_timer.reset()
#
#             if confirm_timer.reached() and res:
#                 return res
#
#             if timeout.reached():
#                 # TODO 抛出异常
#                 return res
#
#     return prefix


