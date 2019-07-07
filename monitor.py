#! env python3

import docker
import yaml
from operator import attrgetter

client = docker.from_env()

def check_service(target_service, service_config):
    update_state = target_service.attrs.get('UpdateStatus', {}).get('State')
    if update_state != 'completed':
        return True

    service_name = target_service.name
    replicas = target_service.attrs.get('Spec', {}).get('Mode', {}).get('Replicated', {}).get('Replicas')
    containers = client.containers.list(filters={ 'label': 'com.docker.swarm.service.name=%s' % service_name, 'status': 'running' })

    if len(containers) != replicas:

        return False

    return True

def format_report_stats(service_name, stats={}):
    mem_stats = stats.get('memory_stats', {})
    cpu_stats = stats.get('cpu_stats', {})
    cpu_usage = sum(cpu_stats.get('cpu_usage', {}).get('percpu_usage', []))
    cpu_total = cpu_stats.get('cpu_usage', {}).get('total_usage')

    report_stats = {
        '@timestamp':
        'service_name': service_name
        'cpu_num': cpu_stats.get('online_cpus'),
        'cpu_percent': cpu_usage*100/cpu_total,
        'mem_usage': mem_stats.get('usage'),
        'mem_max_usage': stats.get('max_usage'),
        'mem_limit': stats.get('limit'),
    }
    print(stats)

    return report_stats

def report_stats(target_service, service_config):
    service_name = target_service.name
    containers = client.containers.list(filters={ 'label': 'com.docker.swarm.service.name=%s' % service_name, 'status': 'running' })

    stats_list = []
    for container in containers:
        report_stats = format_report_stats(container.stats(stream=False))
        stats_list.append(report_stats)

def monitor_service(service_name, service_config):
    services = client.services.list(filters={ 'name': service_name })
    if len(services):
        check_service(services[0], service_config)
        report_stats(services[0], service_config)


if __name__ == '__main__':
    with open('./conf/app.yml', 'r') as stream:
        config = yaml.load(content, Loader=yaml.Loader)
        for service_name, service_config in config['services'].items():
            monitor_service(service_name, service_config)
