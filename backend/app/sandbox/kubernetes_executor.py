from __future__ import annotations
import re,time,uuid,urllib.request
from app.core.config import settings
from app.storage.s3 import ArtifactStore

class KubernetesSandbox:
    def __init__(self):
        self.available=False
        try:
            from kubernetes import client,config
            try: config.load_incluster_config()
            except Exception: config.load_kube_config()
            self.client=client; self.batch=client.BatchV1Api(); self.available=True
        except Exception: self.client=None
    def run_tests(self,root,timeout=120):
        if not self.available:return None
        from app.sandbox.executor import TestExecution,_parse_pytest
        store=ArtifactStore(); run_id=str(uuid.uuid4()); repo_key=store.put_repo(root,run_id); repo_url=store.presign_get(repo_key)
        out_key=f'runs/{run_id}/test-output.txt'; out_url=store.presign_put(out_key)
        job_name=f'forgeai-{run_id[:12]}'
        V1Job=self.client.V1Job; V1JobSpec=self.client.V1JobSpec; V1PodSpec=self.client.V1PodSpec; V1Container=self.client.V1Container
        init=V1Container(name='fetch',image='curlimages/curl:8.15.0',command=['sh','-c',f"mkdir -p /workspace && curl -fsSL '{repo_url}' | tar xzf - -C /workspace && mv /workspace/repo/* /workspace/ && rm -rf /workspace/repo"])
        main=V1Container(name='runner',image=settings.sandbox_image,command=['sh','-c',f"python -m pytest -q > /workspace/test-output.txt 2>&1; code=$?; python -c \"import urllib.request; urllib.request.urlopen(urllib.request.Request('{out_url}',data=open('/workspace/test-output.txt','rb').read(),method='PUT'))\" || true; exit $code"],resources=self.client.V1ResourceRequirements(requests={'cpu':'250m','memory':'256Mi'},limits={'cpu':f'{settings.sandbox_cpus}','memory':settings.sandbox_memory}))
        pod=V1PodSpec(runtime_class_name=settings.sandbox_runtime_class,restart_policy='Never',init_containers=[init],containers=[main],security_context=self.client.V1PodSecurityContext(run_as_non_root=True,seccomp_profile=self.client.V1SeccompProfile(type='RuntimeDefault')),automount_service_account_token=False)
        job=V1Job(metadata=self.client.V1ObjectMeta(name=job_name,labels={'app':'forgeai-sandbox'}),spec=V1JobSpec(backoff_limit=0,active_deadline_seconds=timeout,ttl_seconds_after_finished=300,template=self.client.V1PodTemplateSpec(metadata=self.client.V1ObjectMeta(labels={'app':'forgeai-sandbox'}),spec=pod)))
        self.batch.create_namespaced_job('forgeai-sandbox',job)
        started=time.perf_counter(); code=1
        try:
            while time.perf_counter()-started<timeout+15:
                j=self.batch.read_namespaced_job(job_name,'forgeai-sandbox');
                if j.status.succeeded: code=0; break
                if j.status.failed: break
                time.sleep(1)
            output=urllib.request.urlopen(out_url,timeout=10).read().decode(errors='replace')[-12000:] if code in (0,1) else 'SANDBOX TIMEOUT'
            p,t=_parse_pytest(output); return TestExecution(p,t,code,output,int((time.perf_counter()-started)*1000))
        finally:
            try:self.batch.delete_namespaced_job(job_name,'forgeai-sandbox',propagation_policy='Background')
            except Exception:pass
