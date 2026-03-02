"""CSS/XPath selectors for Xiaohongshu Creator Center.

Centralized here so UI changes only require updating one file.
"""

# Login page — XHS uses CSS-in-JS, class names are dynamic hashes.
# The QR code is a base64 data-URI <img> inside the login form.
LOGIN_QR_CODE = 'img[src^="data:image/png"]'
# After scan, page navigates away from /login
LOGIN_SUCCESS_INDICATOR = '[class*="user-info"], [class*="creator-home"], .sidebar, [class*="menu"]'

# Creator center navigation
NAV_PUBLISH = 'a[href*="publish"], .publish-btn, [class*="publish"]'
NAV_DATA = 'a[href*="data"], [class*="data-center"]'

# Publish page - text/image post
PUBLISH_TYPE_NOTE = '[class*="note"], [data-type="note"]'
PUBLISH_TITLE_INPUT = 'input[placeholder*="标题"], [class*="title"] input, #title'
PUBLISH_CONTENT_INPUT = (
    '[contenteditable="true"], [class*="content"] [contenteditable], '
    '.ql-editor, [class*="editor"]'
)
PUBLISH_IMAGE_UPLOAD = 'input[type="file"][accept*="image"]'
PUBLISH_TAG_INPUT = '[class*="tag"] input, [placeholder*="标签"], [placeholder*="话题"]'
PUBLISH_SUBMIT_BTN = (
    'button[class*="submit"], button[class*="publish"], '
    '[class*="publish-btn"], button:has-text("发布")'
)

# Post success
PUBLISH_SUCCESS = '[class*="success"], [class*="published"]'

# Account info
ACCOUNT_NICKNAME = '[class*="nickname"], [class*="user-name"]'
ACCOUNT_FOLLOWER = '[class*="follower"], [class*="fans"]'
ACCOUNT_FOLLOWING = '[class*="following"]'
ACCOUNT_AVATAR = '[class*="avatar"] img'

# Analytics
ANALYTICS_VIEWS = '[class*="read"], [class*="view"]'
ANALYTICS_LIKES = '[class*="like"]'
ANALYTICS_COMMENTS = '[class*="comment"]'
ANALYTICS_FAVORITES = '[class*="collect"], [class*="favorite"]'
ANALYTICS_SHARES = '[class*="share"]'
