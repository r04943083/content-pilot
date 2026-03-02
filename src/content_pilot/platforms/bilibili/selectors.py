"""CSS/XPath selectors for Bilibili Member Center."""

# Login
LOGIN_QR_CODE = 'img[class*="qrcode"], canvas.qrcode, .login-scan-box img'
LOGIN_SUCCESS_INDICATOR = '[class*="user-info"], .header-user, .nav-user-center'

# Navigation
NAV_PUBLISH = 'a[href*="upload"], [class*="upload"]'
NAV_DATA = 'a[href*="data"], [class*="data"]'

# Video upload page
PUBLISH_VIDEO_UPLOAD = 'input[type="file"][accept*="video"]'
PUBLISH_IMAGE_UPLOAD = 'input[type="file"][accept*="image"]'
PUBLISH_TITLE_INPUT = (
    'input[placeholder*="标题"], .video-title input, '
    '#videoTitle, [class*="title-input"]'
)
PUBLISH_DESC_INPUT = (
    'textarea[placeholder*="简介"], .video-desc textarea, '
    '[class*="desc-input"] textarea, [contenteditable="true"]'
)
PUBLISH_TAG_INPUT = (
    '[class*="tag"] input, [placeholder*="标签"], '
    'input[placeholder*="按回车添加标签"]'
)
PUBLISH_CATEGORY_SELECT = '[class*="type-select"], [class*="category"]'
PUBLISH_SUBMIT_BTN = (
    'button[class*="submit"], .submit-add, '
    'button:has-text("投稿"), button:has-text("发布")'
)

# Article (专栏) publish
ARTICLE_TITLE_INPUT = 'input[placeholder*="标题"], .article-title input'
ARTICLE_CONTENT_INPUT = '[contenteditable="true"], .ql-editor, .editor-content'
ARTICLE_SUBMIT_BTN = 'button:has-text("发布"), [class*="submit"]'

# Success
PUBLISH_SUCCESS = '[class*="success"], .upload-success'

# Account info
ACCOUNT_NICKNAME = '[class*="nickname"], .h-name, .uname'
ACCOUNT_FOLLOWER = '[class*="follower"], .n-fs, [title*="粉丝"]'
ACCOUNT_FOLLOWING = '[class*="following"], .n-gz'
ACCOUNT_AVATAR = '[class*="avatar"] img, .h-avatar img'

# Analytics
ANALYTICS_VIEWS = '[class*="play"], [class*="view"], .play-num'
ANALYTICS_LIKES = '[class*="like"], .like-num'
ANALYTICS_COMMENTS = '[class*="comment"], .reply-num'
ANALYTICS_FAVORITES = '[class*="collect"], [class*="fav"], .fav-num'
ANALYTICS_SHARES = '[class*="share"], .share-num'
ANALYTICS_COINS = '[class*="coin"], .coin-num'
ANALYTICS_DANMAKU = '[class*="danmaku"], .dm-num'
