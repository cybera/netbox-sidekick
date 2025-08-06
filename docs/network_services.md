# Network Services

Network Services are services that are offered to members, such as
Peering, Transit, and R&E.

Sidekick provides a few models to manage network service administration. These models do not actually interact with your network equipment -- they only provide data management to organize your network services.

* Logical System: Inventory/list of the Logical Systems in your routers. For example: peering, research, transit.
* Routing Type: Inventory/list of the different routing types of your members. For example: static, BGP.
* Service Type: Inventory/list of the different types of network services. For example: Peering, Transit, Virtual Firewall.
* Network Service: A member's subscription to a service. If a member subscribes to a Peering service, you will add a new Network service to netbox to describe this.
* Network Service Device: A physical connection on a network device that implements the member's service subscription. A Network Service (subscription) can have one or more Network Service Devices.
* Network Service L3: L3 information about a Network Service Device.
* Network Service L2: L2 information about a Network Service Device.

## Create Network Services

To create Network Services, use the Django Admin page.

## Service Groups

Sidekick includes a model called `NetworkServiceGroup`. This can be used to group member services
together in a common theme. For example, you can create a Group called `All Peering Members` and
then add all Network Services of Peering subscriptions to this group.
