
1.  虚机建立后插入硬盘。 此处的vda是我们希望vm中的硬盘名称"insert_data_disk.sh vn_name vda":
        ```
        $ insert_data_disk.sh ceph_test_0.6.2_01 vda
        Target     Source
        ------------------------------------------------
        hda        /mnt/images/ceph_test_0.6.0_04.raw
        hdb        /mnt/images/Ceph-CentOS-07.0.x86_64-0.6.0.install.iso

        Device attached successfully

        Target     Source
        ------------------------------------------------
        hda        /mnt/images/ceph_test_0.6.0_04.raw
        hdb        /mnt/images/Ceph-CentOS-07.0.x86_64-0.6.0.install.iso
        vda        /mnt/images/ceph_data_0.6.0_04_vda.raw
        ```
        **libvirt实际会根据已有硬盘个数，重命名为vdX**，下述脚本操作的硬盘以日志结尾的新增的target硬盘为准，例如上面的"vda        /mnt/images/ceph_data_0.6.0_04_vda.raw"

2.  libvirt helper: vm.sh
    1.  ssh: 支持复制ss key并ssh连接。
    2.  ip: 调用get_ip.sh得到vm的ip地址。
    3.  ips: 使用grep得到一组虚机的ip地址。
    4.  list: 列出所有虚机。
    5.  tidb helper:
        1.  tidb_mysql: 连接tidb建立的mysql
        2.  pd, tikv, tidb: 重启tidb相关服务并查看日志。

3.  install_kiwi_remote.sh把同目录的install_kiwi.sh复制到目标机器，并执行，install_kiwi.sh的流程包括（每个步骤都可以用"-m xxx"单独执行）：
    1.  init: 初始化。安装kiwi build环境所需的rpm包，git clone kiwi的配置文件(kiwi-descriptions)。
    2.  rebase: rebase kiwi-descriptions本地commit。为了保证不同节点构建一致性，不建议使用。
    3.  checkout: git checkout $commitid。
    4.  update installed rpm packages.
    5.  precheck: 检查kiwi build环境
    6.  build：首先检查$APPLIANCE下有无prepare.sh，如果有传递剩余参数给它，并执行之。用于定制kiwi当前config.xml无法满足的需求。

4.  定制kiwi
    1.  rpms, binaries, root fs

5.  config.xml修改
    1.  默认配置文件
    2.  使用lvm分区
    3.  添加包。build include
    4.  修改网卡名称
        1.  修改"kiwi-descriptions/centos/x86_64/ceph-applicance/root/etc/sysconfig/network-scripts"的脚本。
        2.  如果需要添加udev规则修改网卡名称。
    5.  不弹出选择界面，默认选择默认磁盘安装。如果不写oem-unattended-id, kiwi会直接安装在找到的第一个硬盘上。根据[kiwi的文档](https://suse.github.io/kiwi/development/schema.html#id175)，id是grep "/dev/disks/by-*/*", "/dev/mapper/*"的结果。
        ```
        <oemconfig>
            <oem-unattended>true</oem-unattended>
            <oem-unattended-id>by-id-disk-name</oem-unattended-id>
        </oemconfig>
        ```

