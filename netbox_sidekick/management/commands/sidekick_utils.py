from django.contrib.auth.models import User

from secrets.models import UserKey


VALID_INTERFACE_NAMES = [
    # Arista
    'Ethernet', 'Vlan',

    # Juniper
    'ae', 'et', 'ge', 'lt', 'xe',
]


def decrypt_secret(device, name, user, private_key_path):
    private_key = None
    with open(private_key_path) as f:
        private_key = f.read()

    try:
        _user = User.objects.get(username=user)
    except User.DoesNotExist:
        raise Exception(f"Unable to find user {user}")
        return

    try:
        user_key = UserKey.objects.get(user=_user)
    except UserKey.DoesNotExist:
        raise Exception(f"Unable to find UserKey for {user}")
        return

    master_key = user_key.get_master_key(private_key)
    if master_key is None:
        raise Exception(f"Invalid private key {private_key_path}")
        return

    secret = device.secrets.filter(name=name)
    if len(secret) == 1:
        s = secret[0]
        s.decrypt(master_key)
        return s.plaintext
