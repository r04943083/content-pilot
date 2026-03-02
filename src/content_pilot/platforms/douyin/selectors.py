"""CSS/XPath selectors for Douyin Creator Center."""

# Login
LOGIN_QR_CODE = 'img[class*="qrcode"], canvas[class*="qr"], .qrcode-image img'
LOGIN_SUCCESS_INDICATOR = '[class*="user-info"], [class*="header-user"], .creator-layout'

# Navigation
NAV_PUBLISH = 'a[href*="publish"], [class*="upload"]'
NAV_DATA = 'a[href*="data"], [class*="data"]'

# Publish page - video upload
PUBLISH_VIDEO_UPLOAD = 'input[type="file"][accept*="video"]'
PUBLISH_IMAGE_UPLOAD = 'input[type="file"][accept*="image"]'
PUBLISH_TITLE_INPUT = (
    'input[placeholder*="标题"], [class*="title"] input, '
    '[class*="caption"] input'
)
PUBLISH_DESC_INPUT = (
    '[contenteditable="true"], [class*="description"] textarea, '
    'textarea[placeholder*="描述"], .ql-editor'
)
PUBLISH_TAG_INPUT = '[class*="tag"] input, [placeholder*="话题"], input[placeholder*="#"]'
PUBLISH_SUBMIT_BTN = (
    'button[class*="submit"], button[class*="publish"], '
    'button:has-text("发布")'
)

# Success
PUBLISH_SUCCESS = '[class*="success"], [class*="published"]'

# Account info
ACCOUNT_NICKNAME = '[class*="nickname"], [class*="user-name"]'
ACCOUNT_FOLLOWER = '[class*="follower"], [class*="fans"]'
ACCOUNT_AVATAR = '[class*="avatar"] img'

# Analytics
ANALYTICS_VIEWS = '[class*="play"], [class*="view"]'
ANALYTICS_LIKES = '[class*="like"], [class*="digg"]'
ANALYTICS_COMMENTS = '[class*="comment"]'
ANALYTICS_SHARES = '[class*="share"]'
