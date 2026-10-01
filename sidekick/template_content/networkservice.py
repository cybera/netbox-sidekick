from netbox.plugins import PluginTemplateExtension


class NetworkServiceGraph(PluginTemplateExtension):
    models = ['sidekick.networkservice']

    def right_page(self):
        return self.render('sidekick/template_content/network_service_graph.html')

    def full_width_page(self):
        return self.render('sidekick/template_content/network_service_bandwidth_history.html')


class NetworkServiceGroupGraph(PluginTemplateExtension):
    models = ['sidekick.networkservicegroup']

    def full_width_page(self):
        return self.render('sidekick/template_content/network_service_group_graph.html')
