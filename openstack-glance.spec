Name:             openstack-glance
Version:          2013.2
Release:          0.7.b3%{?dist}
Summary:          OpenStack Image Service

Group:            Applications/System
License:          ASL 2.0
URL:              http://glance.openstack.org
Source0:          https://launchpad.net/glance/havana/havana-3/+download/glance-2013.2.b3.tar.gz
Source1:          openstack-glance-api.init
Source100:        openstack-glance-api.upstart
Source2:          openstack-glance-registry.init
Source200:        openstack-glance-registry.upstart
Source3:          openstack-glance-scrubber.init
Source300:        openstack-glance-scrubber.upstart
Source4:          openstack-glance.logrotate

#
# patches_base=2013.2.b3
#
Patch0001: 0001-Don-t-access-the-net-while-building-docs.patch
Patch0002: 0002-Use-updated-parallel-install-versions-of-epel-packag.patch
Patch0003: 0003-avoid-the-uneeded-dependency-on-Crypto.Random.patch
Patch0004: 0004-Avoid-NULLs-in-crypto-padding.patch
Patch0005: 0005-Remove-runtime-dep-on-python-pbr.patch
#Patch0006: 0006-Revert-use-oslo.sphinx-and-remove-local-copy-of-doc.patch

BuildArch:        noarch
BuildRequires:    python2-devel
BuildRequires:    python-setuptools
BuildRequires:    intltool
# These are required to build due to the requirements check added
BuildRequires:    python-paste-deploy1.5
BuildRequires:    python-routes1.12
BuildRequires:    python-sqlalchemy0.7
BuildRequires:    python-webob1.0
BuildRequires:    python-pbr
BuildRequires:    python-oslo-sphinx

Requires(post):   chkconfig
Requires(preun):  initscripts
Requires(preun):  chkconfig
Requires(pre):    shadow-utils
Requires:         python-glance = %{version}-%{release}
Requires:         python-glanceclient >= 1:0
Requires:         openstack-utils
BuildRequires:    openstack-utils

%description
OpenStack Image Service (code-named Glance) provides discovery, registration,
and delivery services for virtual disk images. The Image Service API server
provides a standard REST interface for querying information about virtual disk
images stored in a variety of back-end stores, including OpenStack Object
Storage. Clients can register new virtual disk images with the Image Service,
query for information on publicly available disk images, and use the Image
Service's client library for streaming virtual disk images.

This package contains the API and registry servers.

%package -n       python-glance
Summary:          Glance Python libraries
Group:            Applications/System

Requires:         MySQL-python
Requires:         pysendfile
Requires:         python-eventlet
Requires:         python-httplib2
Requires:         python-iso8601
Requires:         python-jsonschema
Requires:         python-migrate
Requires:         python-paste-deploy1.5
Requires:         python-routes1.12
Requires:         python-sqlalchemy0.7
Requires:         python-webob1.0
Requires:         python-crypto
Requires:         pyxattr
Requires:         python-swiftclient
Requires:         python-cinderclient
Requires:         python-keystoneclient
Requires:         python-oslo-config
Requires:         sheepdog

#test deps: python-mox python-nose python-requests
#test and optional store:
#ceph - glance.store.rdb
#python-boto - glance.store.s3

%description -n   python-glance
OpenStack Image Service (code-named Glance) provides discovery, registration,
and delivery services for virtual disk images.

This package contains the glance Python library.

%package doc
Summary:          Documentation for OpenStack Image Service
Group:            Documentation

Requires:         %{name} = %{version}-%{release}

BuildRequires:    python-sphinx10
BuildRequires:    graphviz

# Required to build module documents
BuildRequires:    python-boto
BuildRequires:    python-eventlet

%description      doc
OpenStack Image Service (code-named Glance) provides discovery, registration,
and delivery services for virtual disk images.

This package contains documentation files for glance.

%prep
%setup -q -n glance-%{version}
#sed -i 's/%{version}.b3/%{version}/' PKG-INFO
%patch0001 -p1
%patch0002 -p1
%patch0003 -p1
%patch0004 -p1
%patch0005 -p1
#%patch0006 -p1


# Remove bundled egg-info
rm -rf glance.egg-info
sed -i '/\/usr\/bin\/env python/d' glance/common/config.py glance/common/crypt.py glance/db/sqlalchemy/migrate_repo/manage.py
# versioninfo is missing in f3 tarball
echo %{version} > glance/versioninfo

sed -i '/setuptools_git/d' setup.py
sed -i s/REDHATGLANCEVERSION/%{version}/ glance/version.py
sed -i s/REDHATGLANCERELEASE/%{release}/ glance/version.py

# Remove the requirements file so that pbr hooks don't add it
# to distutils requiers_dist config
rm -rf {test-,}requirements.txt tools/{pip,test}-requires

%build

# Change the default config
openstack-config --set etc/glance-api.conf DEFAULT debug False
openstack-config --set etc/glance-api.conf DEFAULT verbose True
openstack-config --set etc/glance-registry.conf DEFAULT debug False
openstack-config --set etc/glance-registry.conf DEFAULT verbose True
openstack-config --set etc/glance-scrubber.conf DEFAULT debug False
openstack-config --set etc/glance-scrubber.conf DEFAULT verbose True

openstack-config --set etc/glance-registry.conf DEFAULT sql_connection mysql://glance:glance@localhost/glance
openstack-config --set etc/glance-api.conf DEFAULT sql_connection mysql://glance:glance@localhost/glance
# Move authtoken configuration out of paste.ini
openstack-config --del etc/glance-api-paste.ini filter:authtoken admin_tenant_name
openstack-config --del etc/glance-api-paste.ini filter:authtoken admin_user
openstack-config --del etc/glance-api-paste.ini filter:authtoken admin_password
openstack-config --del etc/glance-api-paste.ini filter:authtoken auth_host
openstack-config --del etc/glance-api-paste.ini filter:authtoken auth_port
openstack-config --del etc/glance-api-paste.ini filter:authtoken auth_protocol
#openstack-config --set etc/glance-api.conf paste_deploy flavor keystone
openstack-config --set etc/glance-api.conf keystone_authtoken admin_tenant_name %%SERVICE_TENANT_NAME%%
openstack-config --set etc/glance-api.conf keystone_authtoken admin_user %SERVICE_USER%
openstack-config --set etc/glance-api.conf keystone_authtoken admin_password %SERVICE_PASSWORD%
openstack-config --set etc/glance-api.conf keystone_authtoken auth_host 127.0.0.1
openstack-config --set etc/glance-api.conf keystone_authtoken auth_port 35357
openstack-config --set etc/glance-api.conf keystone_authtoken auth_protocol http
openstack-config --del etc/glance-registry-paste.ini filter:authtoken admin_tenant_name
openstack-config --del etc/glance-registry-paste.ini filter:authtoken admin_user
openstack-config --del etc/glance-registry-paste.ini filter:authtoken admin_password
openstack-config --del etc/glance-registry-paste.ini filter:authtoken auth_host
openstack-config --del etc/glance-registry-paste.ini filter:authtoken auth_port
openstack-config --del etc/glance-registry-paste.ini filter:authtoken auth_protocol
#openstack-config --set etc/glance-registry.conf paste_deploy flavor keystone
openstack-config --set etc/glance-registry.conf keystone_authtoken admin_tenant_name %%SERVICE_TENANT_NAME%%
openstack-config --set etc/glance-registry.conf keystone_authtoken admin_user %SERVICE_USER%
openstack-config --set etc/glance-registry.conf keystone_authtoken admin_password %SERVICE_PASSWORD%
openstack-config --set etc/glance-registry.conf keystone_authtoken auth_host 127.0.0.1
openstack-config --set etc/glance-registry.conf keystone_authtoken auth_port 35357
openstack-config --set etc/glance-registry.conf keystone_authtoken auth_protocol http

%{__python} setup.py build

%install
%{__python} setup.py install -O1 --skip-build --root %{buildroot}

# Delete tests
rm -fr %{buildroot}%{python_sitelib}/glance/tests

# Drop old glance CLI it has been deprecated
# and replaced glanceclient
rm -f %{buildroot}%{_bindir}/glance

export PYTHONPATH="$( pwd ):$PYTHONPATH"
pushd doc
sphinx-1.0-build -b html source build/html
sphinx-1.0-build -b man source build/man

mkdir -p %{buildroot}%{_mandir}/man1
install -p -D -m 644 build/man/*.1 %{buildroot}%{_mandir}/man1/
popd

# Fix hidden-file-or-dir warnings
rm -fr doc/build/html/.doctrees doc/build/html/.buildinfo
rm -f %{buildroot}%{_sysconfdir}/glance*.conf
rm -f %{buildroot}%{_sysconfdir}/glance*.ini
rm -f %{buildroot}%{_sysconfdir}/logging.cnf.sample
rm -f %{buildroot}%{_sysconfdir}/policy.json
rm -f %{buildroot}%{_sysconfdir}/schema-image.json
rm -f %{buildroot}/usr/share/doc/glance/README.rst

# Setup directories
install -d -m 755 %{buildroot}%{_datadir}/glance
install -d -m 755 %{buildroot}%{_sharedstatedir}/glance/images

# Config file
install -p -D -m 640 etc/glance-api.conf %{buildroot}%{_sysconfdir}/glance/glance-api.conf
install -p -D -m 640 etc/glance-api-paste.ini %{buildroot}%{_sysconfdir}/glance/glance-api-paste.ini
install -p -D -m 640 etc/glance-registry.conf %{buildroot}%{_sysconfdir}/glance/glance-registry.conf
install -p -D -m 640 etc/glance-registry-paste.ini %{buildroot}%{_sysconfdir}/glance/glance-registry-paste.ini
install -p -D -m 640 etc/glance-cache.conf %{buildroot}%{_sysconfdir}/glance/glance-cache.conf
install -p -D -m 640 etc/glance-scrubber.conf %{buildroot}%{_sysconfdir}/glance/glance-scrubber.conf
install -p -D -m 640 etc/policy.json %{buildroot}%{_sysconfdir}/glance/policy.json
install -p -D -m 640 etc/schema-image.json %{buildroot}%{_sysconfdir}/glance/schema-image.json

# Initscripts
install -p -D -m 755 %{SOURCE1} %{buildroot}%{_initrddir}/openstack-glance-api
install -p -D -m 755 %{SOURCE2} %{buildroot}%{_initrddir}/openstack-glance-registry
install -p -D -m 755 %{SOURCE3} %{buildroot}%{_initrddir}/openstack-glance-scrubber

# Install upstart jobs examples
install -p -m 644 %{SOURCE100} %{buildroot}%{_datadir}/glance/
install -p -m 644 %{SOURCE200} %{buildroot}%{_datadir}/glance/
install -p -m 644 %{SOURCE300} %{buildroot}%{_datadir}/glance/

# Logrotate config
install -p -D -m 644 %{SOURCE4} %{buildroot}%{_sysconfdir}/logrotate.d/openstack-glance

# Install pid directory
install -d -m 755 %{buildroot}%{_localstatedir}/run/glance

# Install log directory
install -d -m 755 %{buildroot}%{_localstatedir}/log/glance

%pre
getent group glance >/dev/null || groupadd -r glance -g 161
getent passwd glance >/dev/null || \
useradd -u 161 -r -g glance -d %{_sharedstatedir}/glance -s /sbin/nologin \
-c "OpenStack Glance Daemons" glance
exit 0

%post
/sbin/chkconfig --add openstack-glance-api
/sbin/chkconfig --add openstack-glance-registry
/sbin/chkconfig --add openstack-glance-scrubber

%preun
if [ $1 = 0 ] ; then
    /sbin/service openstack-glance-api stop >/dev/null 2>&1
    /sbin/chkconfig --del openstack-glance-api
    /sbin/service openstack-glance-registry stop >/dev/null 2>&1
    /sbin/chkconfig --del openstack-glance-registry
    /sbin/service openstack-glance-scrubber stop >/dev/null 2>&1
    /sbin/chkconfig --del openstack-glance-scrubber
fi

%postun
if [ $1 -ge 1 ] ; then
    # Package upgrade, not uninstall
    for svc in api registry scrubber; do
        /sbin/service openstack-glance-${svc} condrestart > /dev/null 2>&1 || :
    done
fi

%files
%doc README.rst
%{_bindir}/glance-api
%{_bindir}/glance-control
%{_bindir}/glance-manage
%{_bindir}/glance-registry
%{_bindir}/glance-cache-cleaner
%{_bindir}/glance-cache-manage
%{_bindir}/glance-cache-prefetcher
%{_bindir}/glance-cache-pruner
%{_bindir}/glance-scrubber
%{_bindir}/glance-replicator
%{_initrddir}/openstack-glance-api
%{_initrddir}/openstack-glance-registry
%{_initrddir}/openstack-glance-scrubber
%dir %{_datadir}/glance
%{_datadir}/glance/openstack-glance-api.upstart
%{_datadir}/glance/openstack-glance-registry.upstart
%{_datadir}/glance/openstack-glance-scrubber.upstart
%{_mandir}/man1/glance*.1.gz
%dir %{_sysconfdir}/glance
%config(noreplace) %attr(-, root, glance) %{_sysconfdir}/glance/glance-api.conf
%config(noreplace) %attr(-, root, glance) %{_sysconfdir}/glance/glance-api-paste.ini
%config(noreplace) %attr(-, root, glance) %{_sysconfdir}/glance/glance-registry.conf
%config(noreplace) %attr(-, root, glance) %{_sysconfdir}/glance/glance-registry-paste.ini
%config(noreplace) %attr(-, root, glance) %{_sysconfdir}/glance/glance-cache.conf
%config(noreplace) %attr(-, root, glance) %{_sysconfdir}/glance/glance-scrubber.conf
%config(noreplace) %attr(-, root, glance) %{_sysconfdir}/glance/policy.json
%config(noreplace) %attr(-, root, glance) %{_sysconfdir}/glance/schema-image.json
%config(noreplace) %attr(-, root, glance) %{_sysconfdir}/logrotate.d/openstack-glance
%dir %attr(0755, glance, nobody) %{_sharedstatedir}/glance
%dir %attr(0755, glance, nobody) %{_localstatedir}/log/glance
%dir %attr(0755, glance, nobody) %{_localstatedir}/run/glance

%files -n python-glance
%doc README.rst
%{python_sitelib}/glance
%{python_sitelib}/glance-%{version}*.egg-info


%files doc
%doc doc/build/html

%changelog
* Sun Sep 15 2013 Dan Prince <dprince@redhat.com> 2013.2.b3
- Add dependency on sheepdog.

* Fri Sep 13 2013 Dan Prince <dprince@redhat.com> 2013.2.b3
- Drop b3 from release name.
- Remove patch 0003 (which drops python-oslo-sphinx)

* Mon Sep  9 2013 John Bresnahan <jbresnah@redhat.com> 2013.2.b3
- Update to 2013.2.b3
- Remove runtime dep on python pbr
- Revert use oslo.sphinx and remove local copy of doc

* Tue Jul 23 2013 John Bresnahan <jbresnah@redhat.com> 2013.2-0.6.b2
- Do not log DEBUG by default
- Do not distribute tests

* Tue Jul 23 2013 Pádraig Brady <pbrady@redhat.com> 2013.2-0.5.b2
- Update to Havana milestone 2
- Depend on python-keystoneclient for auth_token middleware

* Fri Jun  7 2013 John Bresnahan <jbresnah@redhat.com> 2013.2.b1-3
- reinstate EPEL specific patches

* Fri Jun  7 2013 John Bresnahan <jbresnah@redhat.com> 2013.2.b1
- Don't access the net while building docs

* Fri Jun  7 2013 John Bresnahan <jbresnah@redhat.com> 2013.2.b1
- Update to 2013.2.b1

* Mon May 13 2013 Pádraig Brady <P@draigBrady.com> 2013.1-3
- Add the scrubber service for deferred image deletion

* Mon May 13 2013 Pádraig Brady <P@draigBrady.com> 2013.1-2
- Avoid issue with crypto compat patch (#906051)

* Mon Apr 08 2013 Nikola Đipanov <ndipanov@redhat.com> 2013.1-1
- Update to Grizzly final

* Tue Apr  2 2013 Nikola Đipanov <ndipanov@redhat.com> 2013.1-0.8.rc2
- Update to Grizzly RC2

* Tue Mar 22 2013 Nikola Đipanov <ndipanov@redhat.com> 2013.1-0.7.rc1
- Update to Grizzly RC1

* Mon Mar 11 2013 Nikola Đipanov <ndipanov@redhat.com> 2013.1-0.4.g3
- Restart glance service after upgrade

* Mon Feb 25 2013 Nikola Đipanov <ndipanov@redhat.com> 2013.1-0.3.g3
- Update to Grizzlt milestone 3

* Fri Jan 11 2013 Nikola Đipanov <ndipanov@redhat.com> 2013.1-0.2.g2
- Update to Grizzly milestone 2

* Fri Nov 23 2012 Pádraig Brady <P@draigBrady.com> 2013.1-0.1.g1
- Update to Grizzlt milestone 1

* Fri Nov  9 2012 Pádraig Brady <P@draigBrady.com> 2012.2-4
- Fix Glance Authentication bypass for image deletion (CVE-2012-4573)

* Thu Sep 27 2012 Alan Pevec <apevec@redhat.com> 2012.2-2
- Update to folsom final

* Mon Jul  9 2012 Pádraig Brady <P@draigBrady.com> - 2012.1.1-1
- Update to stable/essex 2012.1.1
- Remove world readable bit on sensitive config files
- Include optional upstart jobs

* Tue May 22 2012 Pádraig Brady <P@draigBrady.com> - 2012.1-10
- Fix an issue with glance-manage db_sync (#823702)

* Mon May 21 2012 Pádraig Brady <P@draigBrady.com> - 2012.1-8
- Sync with essex stable
- Don't auto create database on service start
- Remove openstack-glance-db-setup. use openstack-db instead

* Fri May 18 2012 Alan Pevec <apevec@redhat.com> - 2012.1-7
- Drop hard dep on python-kombu, notifications are configurable

* Tue May 01 2012 Pádraig Brady <P@draigBrady.com> - 2012.1-6
- Start the services later in the boot sequence

* Wed Apr 25 2012 Pádraig Brady <P@draigBrady.com> - 2012.1-5
- Use parallel installed versions of python-routes and python-paste-deploy

* Wed Apr 25 2012 Pádraig Brady <P@draigBrady.com> - 2012.1-4
- Fix leak of swift objects on deletion

* Tue Apr 10 2012 Pádraig Brady <P@draigBrady.com> - 2012.1-3
- Fix db setup script to correctly start mysqld

* Tue Apr 10 2012 Pádraig Brady <P@draigBrady.com> - 2012.1-2
- Fix startup failure due to a file ownership issue (#811130)

* Mon Apr  9 2012 Pádraig Brady <P@draigBrady.com> - 2012.1-1
- Update to Essex final

* Mon Feb 13 2012 Russell Bryant <rbryant@redhat.com> - 2011.3.1-3
- Add dependency on python-crypto. (rhbz#789943)

* Thu Jan 26 2012 Russell Bryant <rbryant@redhat.com> - 2011.3.1-2
- Add python-migrate dependency to python-glance (rhbz#784891)

* Fri Jan 20 2012 Pádraig Brady <P@draigBrady.com> - 2011.3.1-1
- Update to 2011.3.1 final

* Wed Jan 18 2012 Mark McLoughlin <markmc@redhat.com> - 2011.3.1-0.2.1063%{?dist}
- Update to latest 2011.3.1 release candidate

* Tue Jan 17 2012 Mark McLoughlin <markmc@redhat.com> - 2011.3.1-0.1.1062%{?dist}
- Update to 2011.3.1 release candidate
- Includes 6 new patches from upstream

* Fri Jan  6 2012 Pádraig Brady <P@draigBrady.com> - 2011.3-6
- Reapply patch to use parallel install versions of epel packages

* Fri Jan  6 2012 Mark McLoughlin <markmc@redhat.com> - 2011.3-5
- Rebase to latest upstream stable/diablo branch adding ~20 patches

* Tue Dec 20 2011 David Busby <oneiroi@fedoraproject.org> - 2011.3-4
- Depend on python-httplib2

* Tue Nov 22 2011 Pádraig Brady <P@draigBrady.com> - 2011.3-3
- Use updated parallel install versions of epel packages

* Tue Nov 22 2011 Pádraig Brady <P@draigBrady.com> - 2011.3-2
- Ensure the docs aren't built with the system glance module
- Ensure we don't access the net when building docs
- Depend on python-paste-deploy (#759512)

* Tue Sep 27 2011 Mark McLoughlin <markmc@redhat.com> - 2011.3-1
- Update to Diablo final

* Tue Sep  6 2011 Mark McLoughlin <markmc@redhat.com> - 2011.3-0.8.d4
- fix DB path in config
- add BR: intltool for distutils-extra

* Wed Aug 31 2011 Angus Salkeld <asalkeld@redhat.com> - 2011.3-0.7.d4
- Use the available man pages
- don't make service files executable
- delete unused files
- add BR: python-distutils-extra (#733610)

* Tue Aug 30 2011 Angus Salkeld <asalkeld@redhat.com> - 2011.3-0.6.d4
- Change from LSB scripts to systemd service files (#732689).

* Fri Aug 26 2011 Mark McLoughlin <markmc@redhat.com> - 2011.3-0.5.d4
- Update to diablo4 milestone
- Add logrotate config (#732691)

* Wed Aug 24 2011 Mark McLoughlin <markmc@redhat.com> - 2011.3-0.4.992bzr
- Update to latest upstream
- Use statically assigned uid:gid 161:161 (#732687)

* Mon Aug 22 2011 Mark McLoughlin <markmc@redhat.com> - 2011.3-0.3.987bzr
- Re-instate python2-devel BR (#731966)

* Mon Aug 22 2011 Mark McLoughlin <markmc@redhat.com> - 2011.3-0.2.987bzr
- Fix rpmlint warnings, reduce macro usage (#731966)

* Wed Aug 17 2011 Mark McLoughlin <markmc@redhat.com> - 2011.3-0.1.987bzr
- Update to latest upstream
- Require python-kombu for new notifiers support

* Mon Aug  8 2011 Mark McLoughlin <markmc@redhat.com> - 2011.3-0.1.967bzr
- Initial package from Alexander Sakhnov <asakhnov@mirantis.com>
  with cleanups by Mark McLoughlin
