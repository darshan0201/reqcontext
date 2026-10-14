"""Two upload paths with different latency requirements."""
from retry import retry_call


def background_upload(client, data):
    """Upload queued data; currently one attempt."""
    return client.upload(data)


def foreground_upload(client, data):
    """Upload user data synchronously."""
    return client.upload(data)
