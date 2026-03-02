"""CSS/XPath selectors for Weibo."""

# Login
LOGIN_QR_CODE = 'img[class*="qrcode"], .qrcode img, [node-type="qrcode"] img'
LOGIN_SUCCESS_INDICATOR = '[class*="gn_name"], .S_txt1, [class*="username"]'

# Navigation
NAV_COMPOSE = '[class*="compose"], [node-type="compose"]'

# Publish
PUBLISH_CONTENT_INPUT = (
    '[contenteditable="true"], textarea[class*="textarea"], '
    '.W_input, [node-type="textEl"]'
)
PUBLISH_IMAGE_UPLOAD = 'input[type="file"][accept*="image"]'
PUBLISH_VIDEO_UPLOAD = 'input[type="file"][accept*="video"]'
PUBLISH_TOPIC_BTN = '[class*="topic"], [node-type="topic"]'
PUBLISH_TOPIC_INPUT = '[class*="topic"] input, input[placeholder*="话题"]'
PUBLISH_SUBMIT_BTN = (
    'button[class*="submit"], [node-type="submit"], '
    'a[class*="send"], button:has-text("发布")'
)

# Success
PUBLISH_SUCCESS = '[class*="success"], [class*="published"]'

# Account info
ACCOUNT_NICKNAME = '[class*="username"], .gn_name, [class*="pf_name"]'
ACCOUNT_FOLLOWER = '[class*="follower"], .S_line1 [href*="fans"]'
ACCOUNT_FOLLOWING = '[class*="following"], .S_line1 [href*="follow"]'
ACCOUNT_AVATAR = '[class*="avatar"] img, .pf_photo img'

# Analytics
ANALYTICS_VIEWS = '[class*="read"], [class*="view"]'
ANALYTICS_LIKES = '[class*="like"]'
ANALYTICS_COMMENTS = '[class*="comment"]'
ANALYTICS_SHARES = '[class*="forward"], [class*="repost"]'
