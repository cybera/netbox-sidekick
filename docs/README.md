# netbox-sidekick

> This plugin is in heavy development and will have breaking changes.
> There's a good chance this plugin might not end up being used long-term,
> either. Please use at your own risk.

# Introduction

This plugin contains various Django models and tools that extends NetBox
to help you manage an NREN. A lot of this functionality is very specific
to managing an NREN - specifically, how Cybera manages its members and
devices.

The models in this plugin reference the core NetBox models but do not
override or customize them. For example: instead of extending NetBox's
"tenant" models with additional information that would be useful for
membership management, this plugin has a Member model with has a
one-to-one relationship with a NetBox tenant. This way, you can still
use NetBox's tenant feature to apply ownership to different devices and
services, but have NREN-specific details safely decoupled in the Member
model.

We've opted to use a plugin instead of using NetBox's custom fields for
the following reasons:

1. Custom fields can't easily handle one-to-many relationships. For
   example, a Tenant/Member can subscribe to multiple services.

2. Keeping all data localized to a plugin makes it easier to
   revert/remove this later on without destroying your existing NetBox
   environment.

# General

* [Installation](./install.md)
* [Models](./models.md)
* [Development](./development.md)

# Sidekick Resources

* [Devices](./devices.md)
* [Members](./members.md)
* [Contacts](./contacts.md)
