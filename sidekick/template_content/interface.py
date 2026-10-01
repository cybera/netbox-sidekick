from netbox.plugins import PluginTemplateExtension

from sidekick.models import NIC


class InterfaceNICPanel(PluginTemplateExtension):
    """
    Render sidekick NIC statistics and traffic graphs on the dcim.Interface
    detail page (replaces the former standalone NIC detail view).
    """
    models = ['dcim.interface']

    def right_page(self):
        nic = NIC.objects.filter(interface_id=self.context['object'].pk).first()
        if nic is None:
            return ''
        return self.render('sidekick/template_content/interface_nic.html', extra_context={'nic': nic})
