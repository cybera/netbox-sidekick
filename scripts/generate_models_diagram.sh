#!/bin/bash

cd ~/netbox/netbox
python manage.py graph_models netbox_sidekick > ~/output.dot
dot -Tpng ~/output.dot -o ~/netbox-sidekick/docs/img/models.png
rm ~/output.dot
