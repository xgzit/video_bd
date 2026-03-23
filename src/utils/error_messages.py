"""
youtobe_bd 用户友好错误提示模块
将技术性错误消息转换为用户可理解的提示
"""
from typing import Dict, Optional, Tuple
import re

from src.core.exceptions import (
    YouTubeDownloaderError, VideoParseError, VideoUnavailableError,
    VideoPrivateError, VideoAgeRestrictedError, VideoLiveError,
    DownloadError, NetworkError, CookieError, BinaryError
)


class ErrorMessages:
    """错误消息管理器"""
    
    # 错误模式到用户友好消息的映射
    ERROR_PATTERNS: Dict[str, Tuple[str, str]] = {
        # 视频相关错误
        'Video unavailable': (
            '视频不可用',
            '该视频可能已被删除、设为私密或在您所在的地区不可用。'
        ),
        'This video is unavailable': (
            '视频不可用',
            '该视频可能已被删除、设为私密或在您所在的地区不可用。'
        ),
        'This video is private': (
            '私人视频',
            '这是一个私人视频，需要登录并获得视频所有者的授权才能观看。请设置 Cookie 后重试。'
        ),
        'Sign in to confirm your age': (
            '年龄限制',
            '此视频有年龄限制，需要登录验证年龄。请在 Cookie 页面设置您的浏览器 Cookie 后重试。'
        ),
        "Sign in to confirm you're not a bot": (
            '需要身份验证',
            'YouTube 检测到自动化访问，需要身份验证。请在 Cookie 页面设置您的浏览器 Cookie 后重试。'
        ),
        "confirm you're not a bot": (
            '需要身份验证',
            'YouTube 检测到自动化访问，需要身份验证。请在 Cookie 页面设置您的浏览器 Cookie 后重试。'
        ),
        'Video is age restricted': (
            '年龄限制',
            '此视频有年龄限制。请设置 Cookie 后重试。'
        ),
        'This live event will begin': (
            '直播未开始',
            '这是一个预定的直播，目前还未开始。请等待直播开始后再尝试下载。'
        ),
        'Premieres in': (
            '首映未开始',
            '这是一个首映视频，目前还未发布。请等待首映结束后再尝试下载。'
        ),
        'is streaming live': (
            '正在直播',
            '该视频正在直播中，无法下载。请等待直播结束后再尝试。'
        ),
        'members-only': (
            '会员专属',
            '这是会员专属内容。您需要是该频道的会员才能观看。请使用会员账号的 Cookie 后重试。'
        ),
        'Join this channel': (
            '会员专属',
            '这是会员专属内容。您需要加入该频道会员才能观看。'
        ),
        
        # 网络相关错误
        'HTTP Error 429': (
            '请求过于频繁',
            '您的请求过于频繁，YouTube 暂时限制了访问。请稍等几分钟后再试。'
        ),
        'Too Many Requests': (
            '请求过于频繁',
            '请求过于频繁，请稍后再试。建议等待 5-10 分钟。'
        ),
        'Connection reset': (
            '连接中断',
            '网络连接中断。请检查您的网络连接，然后重试。'
        ),
        'Connection refused': (
            '连接被拒绝',
            '无法连接到服务器。请检查您的网络设置和代理配置。'
        ),
        'Connection timed out': (
            '连接超时',
            '连接服务器超时。请检查您的网络连接，或尝试使用代理。'
        ),
        'Network is unreachable': (
            '网络不可达',
            '无法访问网络。请确保您已连接到互联网。'
        ),
        'SSL': (
            'SSL 错误',
            '安全连接失败。这可能是由于网络问题或代理设置导致的。'
        ),
        'certificate': (
            '证书错误',
            '安全证书验证失败。如果您使用代理，请检查代理设置。'
        ),
        
        # 格式相关错误
        'No video formats found': (
            '无可用格式',
            '未找到可下载的视频格式。该视频可能受到限制或格式不兼容。'
        ),
        'Requested format is not available': (
            '格式不可用',
            '请求的视频格式不可用。请尝试选择其他格式。'
        ),
        'Unable to extract': (
            '解析失败',
            '无法解析视频信息。请确认链接正确，或稍后重试。'
        ),
        
        # 权限相关错误
        'Permission denied': (
            '权限不足',
            '没有写入权限。请确保下载目录可写，或选择其他保存位置。'
        ),
        'Access denied': (
            '访问被拒绝',
            '访问被拒绝。请检查文件或目录权限。'
        ),
        
        # 空间相关错误
        'No space left': (
            '磁盘空间不足',
            '磁盘空间不足，无法保存文件。请清理磁盘空间后重试。'
        ),
        'Disk quota exceeded': (
            '磁盘配额已满',
            '磁盘配额已满。请清理一些文件后重试。'
        ),
        
        # yt-dlp 相关错误
        'yt-dlp': (
            '下载工具错误',
            '下载工具出现问题。请尝试在"版本"页面更新 yt-dlp。'
        ),
        'ffmpeg': (
            '转换工具错误',
            '视频转换工具出现问题。请尝试在"版本"页面更新 ffmpeg。'
        ),
        
        # JavaScript 运行时相关错误
        'No supported JavaScript runtime': (
            '缺少 JavaScript 运行时',
            'YouTube 现在需要 JavaScript 运行时来提取视频信息。\n\n'
            '请安装以下任一运行时：\n'
            '• Node.js（推荐）：https://nodejs.org/\n'
            '• Deno：https://deno.land/\n\n'
            '安装完成后，请重启应用程序。'
        ),
        'JavaScript runtime': (
            '缺少 JavaScript 运行时',
            '需要安装 JavaScript 运行时才能下载 YouTube 视频。\n\n'
            '推荐安装 Node.js：\n'
            '1. 访问 https://nodejs.org/\n'
            '2. 下载并安装最新 LTS 版本\n'
            '3. 重启应用程序'
        ),
    }
    
    # 建议操作
    SUGGESTIONS: Dict[str, str] = {
        'cookie': '请在"Cookie"页面设置您的浏览器 Cookie。',
        'network': '请检查您的网络连接和代理设置。',
        'retry': '请稍后再试。',
        'update': '请在"版本"页面检查并更新工具。',
        'format': '请尝试选择其他视频格式。',
        'permission': '请检查目录权限或选择其他保存位置。',
        'space': '请清理磁盘空间后重试。',
    }
    
    @classmethod
    def get_user_message(cls, error: str, include_suggestion: bool = True) -> str:
        """
        获取用户友好的错误消息
        
        Args:
            error: 原始错误消息
            include_suggestion: 是否包含建议
            
        Returns:
            用户友好的错误消息
        """
        error_lower = error.lower()
        
        for pattern, (title, message) in cls.ERROR_PATTERNS.items():
            if pattern.lower() in error_lower:
                result = f"{title}\n\n{message}"
                
                if include_suggestion:
                    suggestion = cls._get_suggestion(pattern)
                    if suggestion:
                        result += f"\n\n💡 建议：{suggestion}"
                
                return result
        
        # 默认消息
        return f"下载出错\n\n{error}\n\n💡 建议：如果问题持续，请尝试更新下载工具或检查网络连接。"
    
    @classmethod
    def _get_suggestion(cls, pattern: str) -> str:
        """根据错误模式获取建议"""
        pattern_lower = pattern.lower()
        
        if any(word in pattern_lower for word in ['private', 'age', 'sign in', 'members']):
            return cls.SUGGESTIONS['cookie']
        elif any(word in pattern_lower for word in ['connection', 'network', 'ssl', 'certificate', 'http']):
            return cls.SUGGESTIONS['network']
        elif any(word in pattern_lower for word in ['format', 'extract']):
            return cls.SUGGESTIONS['format']
        elif any(word in pattern_lower for word in ['permission', 'access']):
            return cls.SUGGESTIONS['permission']
        elif any(word in pattern_lower for word in ['space', 'quota']):
            return cls.SUGGESTIONS['space']
        elif any(word in pattern_lower for word in ['yt-dlp', 'ffmpeg']):
            return cls.SUGGESTIONS['update']
        elif 'javascript runtime' in pattern_lower or 'no supported' in pattern_lower:
            return '请安装 Node.js 或 Deno JavaScript 运行时。'
        else:
            return cls.SUGGESTIONS['retry']
    
    @classmethod
    def get_error_title(cls, error: str) -> str:
        """获取错误标题"""
        error_lower = error.lower()
        
        for pattern, (title, _) in cls.ERROR_PATTERNS.items():
            if pattern.lower() in error_lower:
                return title
        
        return "下载出错"
    
    @classmethod
    def from_exception(cls, exception: Exception) -> str:
        """
        从异常获取用户友好消息
        
        Args:
            exception: 异常对象
            
        Returns:
            用户友好的错误消息
        """
        if isinstance(exception, VideoUnavailableError):
            return "视频不可用\n\n该视频可能已被删除、设为私密或在您所在的地区不可用。"
        elif isinstance(exception, VideoPrivateError):
            return "私人视频\n\n这是一个私人视频，需要登录才能访问。请设置 Cookie 后重试。"
        elif isinstance(exception, VideoAgeRestrictedError):
            return "年龄限制\n\n此视频有年龄限制，请设置 Cookie 后重试。"
        elif isinstance(exception, VideoLiveError):
            return "直播视频\n\n无法下载正在进行的直播。请等待直播结束后重试。"
        elif isinstance(exception, NetworkError):
            return "网络错误\n\n请检查您的网络连接后重试。"
        elif isinstance(exception, CookieError):
            return "Cookie 错误\n\n请检查 Cookie 设置是否正确。"
        elif isinstance(exception, BinaryError):
            return "工具错误\n\n下载工具出现问题。请在\"版本\"页面更新工具。"
        elif isinstance(exception, YouTubeDownloaderError):
            return cls.get_user_message(str(exception))
        else:
            return cls.get_user_message(str(exception))
    
    @classmethod
    def is_recoverable(cls, error: str) -> bool:
        """
        判断错误是否可恢复（可以通过重试解决）
        
        Args:
            error: 错误消息
            
        Returns:
            是否可恢复
        """
        recoverable_patterns = [
            'connection', 'timeout', 'network', 'http error 5',
            'temporarily', 'try again', 'rate limit'
        ]
        
        error_lower = error.lower()
        return any(pattern in error_lower for pattern in recoverable_patterns)
    
    @classmethod
    def needs_cookie(cls, error: str) -> bool:
        """
        判断错误是否需要设置 Cookie
        
        Args:
            error: 错误消息
            
        Returns:
            是否需要 Cookie
        """
        cookie_patterns = [
            'private', 'age', 'sign in', 'login', 'members',
            'confirm your age', 'age restricted', 'authentication',
            "confirm you're not a bot", 'not a bot', 'bot'
        ]
        
        error_lower = error.lower()
        return any(pattern in error_lower for pattern in cookie_patterns)


def format_error_for_user(error: str) -> str:
    """
    格式化错误消息供用户查看（便捷函数）
    
    Args:
        error: 原始错误消息
        
    Returns:
        格式化的错误消息
    """
    return ErrorMessages.get_user_message(error)


def format_exception_for_user(exception: Exception) -> str:
    """
    格式化异常供用户查看（便捷函数）
    
    Args:
        exception: 异常对象
        
    Returns:
        格式化的错误消息
    """
    return ErrorMessages.from_exception(exception)

