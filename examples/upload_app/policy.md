# Upload policy
Background upload operations may retry network timeouts up to three attempts.
Foreground uploads must remain responsive; retry behavior needs product review.
A timeout does not establish that the remote upload failed. The uploader must
establish an idempotency strategy before retrying requests with side effects.
