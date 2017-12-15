boilerplate = {}


boilerplate['v1beta1.Ingress'] = lambda: {'kind': 'Ingress', 'apiVersion': 'extensions/v1beta1', 'metadata': {}}
# v1.PortworxVolumeSource has no boilerplate
# v1.ConfigMapVolumeSource has no boilerplate
boilerplate['v1beta1.NetworkPolicyList'] = lambda: {'kind': 'NetworkPolicyList', 'apiVersion': 'extensions/v1beta1', 'metadata': {}}
boilerplate['v1.LimitRange'] = lambda: {'kind': 'LimitRange', 'apiVersion': 'v1', 'metadata': {}}
# v1beta1.SELinuxStrategyOptions has no boilerplate
# v1beta1.CertificateSigningRequestSpec has no boilerplate
# v1.ProjectedVolumeSource has no boilerplate
# v1beta1.RollbackConfig has no boilerplate
# v1.ContainerPort has no boilerplate
boilerplate['v1.Scale'] = lambda: {'kind': 'Scale', 'apiVersion': 'v1', 'metadata': {}}
# v1.QuobyteVolumeSource has no boilerplate
# v1beta1.RollingUpdateDaemonSet has no boilerplate
# v1beta1.ReplicaSetCondition has no boilerplate
# v1.RBDVolumeSource has no boilerplate
boilerplate['v1beta1.ClusterRoleBinding'] = lambda: {'kind': 'ClusterRoleBinding', 'apiVersion': 'rbac.authorization.k8s.io/v1beta1', 'metadata': {}}
# v1beta1.IngressRule has no boilerplate
# v1.EndpointAddress has no boilerplate
boilerplate['v1beta1.Scale'] = lambda: {'kind': 'Scale', 'apiVersion': 'extensions/v1beta1', 'metadata': {}}
# v1.Affinity has no boilerplate
# v1.Capability has no boilerplate
boilerplate['v1.Namespace'] = lambda: {'kind': 'Namespace', 'apiVersion': 'v1', 'metadata': {}}
# v1beta1.DaemonSetStatus has no boilerplate
boilerplate['v1.Service'] = lambda: {'kind': 'Service', 'apiVersion': 'v1', 'metadata': {}}
boilerplate['v1.EndpointsList'] = lambda: {'kind': 'EndpointsList', 'apiVersion': 'v1', 'metadata': {}}
boilerplate['v1beta1.RoleList'] = lambda: {'kind': 'RoleList', 'apiVersion': 'rbac.authorization.k8s.io/v1beta1', 'metadata': {}}
# v1.PersistentVolumeClaimVolumeSource has no boilerplate
# v1.Preconditions has no boilerplate
# v1beta1.IDRange has no boilerplate
# v1beta1.DeploymentCondition has no boilerplate
# v1beta1.FSGroupStrategyOptions has no boilerplate
boilerplate['v1beta1.StorageClassList'] = lambda: {'kind': 'StorageClassList', 'apiVersion': 'storage.k8s.io/v1beta1', 'metadata': {}}
# v1.LocalObjectReference has no boilerplate
# v1.ReplicationControllerCondition has no boilerplate
# v1.Capabilities has no boilerplate
boilerplate['v1beta1.CertificateSigningRequest'] = lambda: {'kind': 'CertificateSigningRequest', 'apiVersion': 'certificates.k8s.io/v1beta1', 'metadata': {}}
# v1.EnvVarSource has no boilerplate
boilerplate['v1.PodList'] = lambda: {'kind': 'PodList', 'apiVersion': 'v1', 'metadata': {}}
boilerplate['v1.SecretList'] = lambda: {'kind': 'SecretList', 'apiVersion': 'v1', 'metadata': {}}
# v1.AzureDiskVolumeSource has no boilerplate
# v1beta1.HTTPIngressRuleValue has no boilerplate
# v1.PodAffinityTerm has no boilerplate
boilerplate['v1beta1.ClusterRoleBindingList'] = lambda: {'kind': 'ClusterRoleBindingList', 'apiVersion': 'rbac.authorization.k8s.io/v1beta1', 'metadata': {}}
# v1.ISCSIVolumeSource has no boilerplate
# v1.VsphereVirtualDiskVolumeSource has no boilerplate
boilerplate['v1.LimitRangeList'] = lambda: {'kind': 'LimitRangeList', 'apiVersion': 'v1', 'metadata': {}}
# v1.NodeSystemInfo has no boilerplate
boilerplate['v1.ConfigMapList'] = lambda: {'kind': 'ConfigMapList', 'apiVersion': 'v1', 'metadata': {}}
boilerplate['v1.Endpoints'] = lambda: {'kind': 'Endpoints', 'apiVersion': 'v1', 'metadata': {}}
# v1.PersistentVolumeClaimSpec has no boilerplate
# v1beta1.RunAsUserStrategyOptions has no boilerplate
# v1.StorageOSPersistentVolumeSource has no boilerplate
# v1.PodAntiAffinity has no boilerplate
# v1.PersistentVolumeClaimStatus has no boilerplate
# v1.ResourceFieldSelector has no boilerplate
boilerplate['v1.ReplicationControllerList'] = lambda: {'kind': 'ReplicationControllerList', 'apiVersion': 'v1', 'metadata': {}}
boilerplate['v1.ConfigMap'] = lambda: {'kind': 'ConfigMap', 'apiVersion': 'v1', 'metadata': {}}
# v1.NodeDaemonEndpoints has no boilerplate
# v1.NodeSelectorRequirement has no boilerplate
boilerplate['v1beta1.ThirdPartyResource'] = lambda: {'kind': 'ThirdPartyResource', 'apiVersion': 'extensions/v1beta1', 'metadata': {}}
# v1.PodSpec has no boilerplate
boilerplate['v1beta1.ReplicaSet'] = lambda: {'kind': 'ReplicaSet', 'apiVersion': 'extensions/v1beta1', 'metadata': {}}
# v1.DownwardAPIProjection has no boilerplate
# v1.NamespaceStatus has no boilerplate
# v1.FCVolumeSource has no boilerplate
# v1.EnvVar has no boilerplate
boilerplate['v1beta1.Role'] = lambda: {'kind': 'Role', 'apiVersion': 'rbac.authorization.k8s.io/v1beta1', 'metadata': {}}
boilerplate['v1beta1.DeploymentRollback'] = lambda: {'kind': 'DeploymentRollback', 'apiVersion': 'extensions/v1beta1'}
# v1.ComponentCondition has no boilerplate
# v1.WatchEvent has no boilerplate
# v1.ServiceSpec has no boilerplate
# v1.DownwardAPIVolumeFile has no boilerplate
# v1.StorageOSVolumeSource has no boilerplate
# v1.SecretKeySelector has no boilerplate
boilerplate['v1beta1.ClusterRoleList'] = lambda: {'kind': 'ClusterRoleList', 'apiVersion': 'rbac.authorization.k8s.io/v1beta1', 'metadata': {}}
boilerplate['v1.PodTemplateList'] = lambda: {'kind': 'PodTemplateList', 'apiVersion': 'v1', 'metadata': {}}
# v1.LabelSelectorRequirement has no boilerplate
boilerplate['v1beta1.DaemonSetList'] = lambda: {'kind': 'DaemonSetList', 'apiVersion': 'extensions/v1beta1', 'metadata': {}}
# v1.SecretVolumeSource has no boilerplate
# v1.Container has no boilerplate
# v1beta1.ReplicaSetStatus has no boilerplate
# v1.NodeAddress has no boilerplate
# v1.FlexVolumeSource has no boilerplate
# v1.ReplicationControllerSpec has no boilerplate
# v1.StatusCause has no boilerplate
# v1.LimitRangeSpec has no boilerplate
# v1.PodCondition has no boilerplate
# v1.HostAlias has no boilerplate
# v1.ContainerStateRunning has no boilerplate
# v1beta1.HTTPIngressPath has no boilerplate
boilerplate['v1beta1.IngressList'] = lambda: {'kind': 'IngressList', 'apiVersion': 'extensions/v1beta1', 'metadata': {}}
boilerplate['v1.StorageClass'] = lambda: {'kind': 'StorageClass', 'apiVersion': 'storage.k8s.io/v1', 'metadata': {}}
# v1.FlockerVolumeSource has no boilerplate
# v1beta1.HostPortRange has no boilerplate
# v1beta1.NetworkPolicyIngressRule has no boilerplate
boilerplate['v1.ComponentStatusList'] = lambda: {'kind': 'ComponentStatusList', 'apiVersion': 'v1', 'metadata': {}}
boilerplate['v1beta1.ClusterRole'] = lambda: {'kind': 'ClusterRole', 'apiVersion': 'rbac.authorization.k8s.io/v1beta1', 'metadata': {}}
# v1.VolumeProjection has no boilerplate
# v1beta1.PolicyRule has no boilerplate
# v1beta1.CertificateSigningRequestStatus has no boilerplate
boilerplate['v1beta1.Deployment'] = lambda: {'kind': 'Deployment', 'apiVersion': 'extensions/v1beta1', 'metadata': {}}
# v1.ConfigMapProjection has no boilerplate
# v1.NamespaceSpec has no boilerplate
# v1.PodAffinity has no boilerplate
# v1.ScaleIOVolumeSource has no boilerplate
boilerplate['v1.PodTemplate'] = lambda: {'kind': 'PodTemplate', 'apiVersion': 'v1', 'metadata': {}}
# v1.DeletionPropagation has no boilerplate
# v1.ObjectMeta has no boilerplate
boilerplate['v1.ResourceQuota'] = lambda: {'kind': 'ResourceQuota', 'apiVersion': 'v1', 'metadata': {}}
# v1.PodStatus has no boilerplate
# v1.LabelSelector has no boilerplate
# v1.Taint has no boilerplate
boilerplate['v1.PersistentVolumeClaim'] = lambda: {'kind': 'PersistentVolumeClaim', 'apiVersion': 'v1', 'metadata': {}}
# v1.ServiceStatus has no boilerplate
# v1.ResourceRequirements has no boilerplate
# v1.AzureFileVolumeSource has no boilerplate
boilerplate['v1.PersistentVolume'] = lambda: {'kind': 'PersistentVolume', 'apiVersion': 'v1', 'metadata': {}}
# v1.PersistentVolumeAccessMode has no boilerplate
# v1beta1.RollingUpdateDeployment has no boilerplate
# v1.ExecAction has no boilerplate
# v1beta1.IngressSpec has no boilerplate
# v1.ContainerStateWaiting has no boilerplate
# v1.AzureDataDiskKind has no boilerplate
# v1.HostPathVolumeSource has no boilerplate
# v1.PersistentVolumeSpec has no boilerplate
# v1.NodeAffinity has no boilerplate
# v1beta1.DaemonSetSpec has no boilerplate
# v1beta1.IngressStatus has no boilerplate
# v1.NodeSelector has no boilerplate
boilerplate['v1beta1.RoleBinding'] = lambda: {'kind': 'RoleBinding', 'apiVersion': 'rbac.authorization.k8s.io/v1beta1', 'metadata': {}}
boilerplate['v1.ServiceAccountList'] = lambda: {'kind': 'ServiceAccountList', 'apiVersion': 'v1', 'metadata': {}}
# v1.Patch has no boilerplate
# v1.EventSource has no boilerplate
boilerplate['v1.Event'] = lambda: {'kind': 'Event', 'apiVersion': 'v1', 'metadata': {}}
boilerplate['v1.ReplicationController'] = lambda: {'kind': 'ReplicationController', 'apiVersion': 'v1', 'metadata': {}}
boilerplate['v1.ResourceQuotaList'] = lambda: {'kind': 'ResourceQuotaList', 'apiVersion': 'v1', 'metadata': {}}
boilerplate['v1beta1.DeploymentList'] = lambda: {'kind': 'DeploymentList', 'apiVersion': 'extensions/v1beta1', 'metadata': {}}
# v1.ContainerStatus has no boilerplate
# v1.ConfigMapKeySelector has no boilerplate
# v1.Protocol has no boilerplate
boilerplate['v1.NodeList'] = lambda: {'kind': 'NodeList', 'apiVersion': 'v1', 'metadata': {}}
boilerplate['v1.Status'] = lambda: {'kind': 'Status', 'apiVersion': 'extensions/v1beta1', 'metadata': {}}
boilerplate['v1.EventList'] = lambda: {'kind': 'EventList', 'apiVersion': 'v1', 'metadata': {}}
# v1.SecretProjection has no boilerplate
# v1.CinderVolumeSource has no boilerplate
boilerplate['v1.StorageClassList'] = lambda: {'kind': 'StorageClassList', 'apiVersion': 'storage.k8s.io/v1', 'metadata': {}}
boilerplate['v1beta1.ThirdPartyResourceList'] = lambda: {'kind': 'ThirdPartyResourceList', 'apiVersion': 'extensions/v1beta1', 'metadata': {}}
# v1.AWSElasticBlockStoreVolumeSource has no boilerplate
boilerplate['v1.ServiceAccount'] = lambda: {'kind': 'ServiceAccount', 'apiVersion': 'v1', 'metadata': {}}
# v1.LimitRangeItem has no boilerplate
# v1beta1.FSType has no boilerplate
boilerplate['v1.PersistentVolumeClaimList'] = lambda: {'kind': 'PersistentVolumeClaimList', 'apiVersion': 'v1', 'metadata': {}}
# types.UID has no boilerplate
# v1.ResourceQuotaSpec has no boilerplate
# v1beta1.NetworkPolicySpec has no boilerplate
boilerplate['v1.OwnerReference'] = lambda: {'kind': 'OwnerReference', 'apiVersion': 'extensions/v1beta1'}
boilerplate['v1beta1.Eviction'] = lambda: {'kind': 'Eviction', 'apiVersion': 'v1', 'metadata': {}}
boilerplate['v1.ServiceList'] = lambda: {'kind': 'ServiceList', 'apiVersion': 'v1', 'metadata': {}}
# v1.ContainerStateTerminated has no boilerplate
# v1beta1.DeploymentSpec has no boilerplate
boilerplate['v1.Node'] = lambda: {'kind': 'Node', 'apiVersion': 'v1', 'metadata': {}}
# v1.WeightedPodAffinityTerm has no boilerplate
boilerplate['v1.DeleteOptions'] = lambda: {'kind': 'DeleteOptions', 'apiVersion': 'extensions/v1beta1'}
# v1.EndpointPort has no boilerplate
boilerplate['v1.PersistentVolumeList'] = lambda: {'kind': 'PersistentVolumeList', 'apiVersion': 'v1', 'metadata': {}}
# v1.HTTPGetAction has no boilerplate
# v1.HTTPHeader has no boilerplate
boilerplate['v1.Secret'] = lambda: {'kind': 'Secret', 'apiVersion': 'v1', 'metadata': {}}
# v1.KeyToPath has no boilerplate
# v1.Handler has no boilerplate
boilerplate['v1beta1.StorageClass'] = lambda: {'kind': 'StorageClass', 'apiVersion': 'storage.k8s.io/v1beta1', 'metadata': {}}
# v1.NodeSelectorTerm has no boilerplate
# v1.ObjectFieldSelector has no boilerplate
boilerplate['v1beta1.NetworkPolicy'] = lambda: {'kind': 'NetworkPolicy', 'apiVersion': 'extensions/v1beta1', 'metadata': {}}
# v1.EndpointSubset has no boilerplate
# v1.TCPSocketAction has no boilerplate
# v1.Initializer has no boilerplate
# v1.NodeCondition has no boilerplate
boilerplate['v1.NamespaceList'] = lambda: {'kind': 'NamespaceList', 'apiVersion': 'v1', 'metadata': {}}
# v1.ContainerImage has no boilerplate
# v1beta1.RoleRef has no boilerplate
# v1.NodeStatus has no boilerplate
# v1.VolumeMount has no boilerplate
# v1.SELinuxOptions has no boilerplate
# v1.UniqueVolumeName has no boilerplate
# v1.GCEPersistentDiskVolumeSource has no boilerplate
# v1.Initializers has no boilerplate
boilerplate['v1beta1.DaemonSet'] = lambda: {'kind': 'DaemonSet', 'apiVersion': 'extensions/v1beta1', 'metadata': {}}
# v1beta1.CertificateSigningRequestCondition has no boilerplate
boilerplate['v1.ObjectReference'] = lambda: {'kind': 'ObjectReference', 'apiVersion': 'v1'}
# v1.SecurityContext has no boilerplate
boilerplate['v1beta1.PodSecurityPolicyList'] = lambda: {'kind': 'PodSecurityPolicyList', 'apiVersion': 'extensions/v1beta1', 'metadata': {}}
boilerplate['v1.ComponentStatus'] = lambda: {'kind': 'ComponentStatus', 'apiVersion': 'v1', 'metadata': {}}
# v1.ConfigMapEnvSource has no boilerplate
boilerplate['v1beta1.ReplicaSetList'] = lambda: {'kind': 'ReplicaSetList', 'apiVersion': 'extensions/v1beta1', 'metadata': {}}
# v1.PreferredSchedulingTerm has no boilerplate
# v1.Lifecycle has no boilerplate
# v1beta1.ScaleSpec has no boilerplate
# v1.ReplicationControllerStatus has no boilerplate
# v1beta1.APIVersion has no boilerplate
# v1.NodeSpec has no boilerplate
# v1beta1.ReplicaSetSpec has no boilerplate
# v1beta1.ScaleStatus has no boilerplate
# v1beta1.NetworkPolicyPeer has no boilerplate
# v1beta1.KeyUsage has no boilerplate
# v1.ServicePort has no boilerplate
# v1beta1.Subject has no boilerplate
# v1.EmptyDirVolumeSource has no boilerplate
# v1beta1.PodSecurityPolicySpec has no boilerplate
boilerplate['v1.Pod'] = lambda: {'kind': 'Pod', 'apiVersion': 'v1', 'metadata': {}}
# v1.CephFSVolumeSource has no boilerplate
boilerplate['v1beta1.PodSecurityPolicy'] = lambda: {'kind': 'PodSecurityPolicy', 'apiVersion': 'extensions/v1beta1', 'metadata': {}}
boilerplate['v1beta1.CertificateSigningRequestList'] = lambda: {'kind': 'CertificateSigningRequestList', 'apiVersion': 'certificates.k8s.io/v1beta1', 'metadata': {}}
# v1.APIResource has no boilerplate
# v1beta1.DeploymentStrategy has no boilerplate
# v1beta1.DeploymentStatus has no boilerplate
# v1.GlusterfsVolumeSource has no boilerplate
# v1.DaemonEndpoint has no boilerplate
boilerplate['v1.Binding'] = lambda: {'kind': 'Binding', 'apiVersion': 'v1', 'metadata': {}}
# v1.Volume has no boilerplate
# v1.ListMeta has no boilerplate
# v1.ContainerState has no boilerplate
boilerplate['v1beta1.RoleBindingList'] = lambda: {'kind': 'RoleBindingList', 'apiVersion': 'rbac.authorization.k8s.io/v1beta1', 'metadata': {}}
# v1.DownwardAPIVolumeSource has no boilerplate
# v1.ScaleSpec has no boilerplate
# v1.LoadBalancerIngress has no boilerplate
# v1.FinalizerName has no boilerplate
boilerplate['v1.PodTemplateSpec'] = lambda: {'metadata': {}}
# v1.AzureDataDiskCachingMode has no boilerplate
# v1beta1.DaemonSetUpdateStrategy has no boilerplate
# v1.GitRepoVolumeSource has no boilerplate
# v1.Probe has no boilerplate
# v1.ResourceQuotaStatus has no boilerplate
# v1beta1.SupplementalGroupsStrategyOptions has no boilerplate
# v1.PhotonPersistentDiskVolumeSource has no boilerplate
# v1.LocalVolumeSource has no boilerplate
# v1.SecretEnvSource has no boilerplate
# v1beta1.NetworkPolicyPort has no boilerplate
# v1.Toleration has no boilerplate
# v1.ResourceQuotaScope has no boilerplate
# v1beta1.IngressBackend has no boilerplate
# v1.PodSecurityContext has no boilerplate
# v1.ScaleStatus has no boilerplate
# v1.StatusDetails has no boilerplate
# v1.LoadBalancerStatus has no boilerplate
# v1.NFSVolumeSource has no boilerplate
# v1.AttachedVolume has no boilerplate
# v1beta1.IngressTLS has no boilerplate
# v1.PersistentVolumeStatus has no boilerplate
boilerplate['v1.APIResourceList'] = lambda: {'kind': 'APIResourceList', 'apiVersion': 'extensions/v1beta1'}
# v1.EnvFromSource has no boilerplate
