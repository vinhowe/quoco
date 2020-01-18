# API

## Important considerations:

#### IDs need to be encrypted before being sent to the end user (post-MVP).

Maybe Datastore entities should store encrypted versions of their keys? This way, we only have to encrypt them once. These would have to be regenerated whenever the encryption key changed.
