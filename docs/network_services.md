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

## Importing Network Services

There are two ways to import Network Services:

1. Manually through the Django Admin page.
2. Using import scripts.

### Import Scripts

The import scripts provided will most likely not work out of the box for you, so you'll have to modify them. Review where your existing Network Service data is stored, how you will export it, and how each exported service and field will map to Sidekick.

### CMDB / NetHarbour

Cybera's original network service application was [CMDB/Netharbour](https://github.com/netharbour/netharbour). To export network services, the following MySQL queries were used:

```sql
select * from Services inner join contact_groups on Services.cust_id=contact_groups.group_id inner join Service_types on Services.service_type=Service_types.service_type_id;

select * from Services_Interfaces;

select service_id, L3_service_details.* from Services inner join L3_service_details on Services.l3_service_id=L3_service_details.l3_service_id;


elect service_id, L2_service_details.* from Services inner join L2_service_details on Services.l2_service_id=L2_service_details.l2_service_id;
```
