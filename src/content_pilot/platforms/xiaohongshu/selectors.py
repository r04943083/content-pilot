"""CSS/XPath selectors for Xiaohongshu Creator Center.

Centralized here so UI changes only require updating one file.
XHS uses CSS-in-JS — class names with "css-" prefix are dynamic hashes and
should not be relied on. Use stable attributes like placeholder, data-*, or
semantic class names that ship with the component library.
"""

# Login page
# The QR code is a base64 data-URI <img> inside the login form.
LOGIN_QR_CODE = 'img[src^="data:image/png"]'

# Publish page — tabs
PUBLISH_TAB_IMAGE = 'span.title'  # filter by text "上传图文" in code

# Publish page — file upload (accept changes per active tab)
PUBLISH_IMAGE_UPLOAD = 'input.upload-input'

# Publish page — editor (appears after uploading at least one image)
PUBLISH_TITLE_INPUT = 'input[placeholder*="标题"]'
PUBLISH_CONTENT_INPUT = '.tiptap.ProseMirror[contenteditable="true"]'
PUBLISH_TOPIC_BTN = 'button.topic-btn'
PUBLISH_SUBMIT_BTN = 'button:has-text("发布")'

# Post success — URL changes or a success toast appears
PUBLISH_SUCCESS = '[class*="success"], [class*="published"]'

# Account info (creator home, after login)
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
