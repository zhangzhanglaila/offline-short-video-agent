"""模板渲染相关异常"""


class TemplateError(Exception):
    """模板系统基础异常"""
    pass


class TemplateNotFoundError(TemplateError):
    """模板不存在"""
    pass


class TemplateRenderError(TemplateError):
    """模板渲染失败"""
    pass


class BrowserNotAvailableError(TemplateError):
    """浏览器不可用"""
    pass