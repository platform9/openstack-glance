Name:             openstack-glance
Version:          2012.1
Release:          6%{?dist}
Summary:          OpenStack Image Service

Group:            Applications/System
License:          ASL 2.0
URL:              http://glance.openstack.org
Source0:          https://launchpad.net/glance/essex/2012.1/+download/glance-%{version}.tar.gz
Source1:          openstack-glance-api.service
Source2:          openstack-glance-registry.service
Source3:          openstack-glance.logrotate
Source4:          openstack-glance-db-setup

#
# patches_base=2012.1
#
Patch0001: 0001-Ensure-swift-auth-URL-includes-trailing-slash.patch
Patch0002: 0002-search-for-logger-in-PATH.patch
Patch0003: 0003-Fix-content-type-for-qpid-notifier.patch
Patch0004: 0004-Omit-Content-Length-on-chunked-transfer.patch
Patch0005: 0005-Fix-i18n-in-glance.notifier.notify_kombu.patch
Patch0006: 0006-Don-t-access-the-net-while-building-docs.patch
Patch0007: 0007-Support-DB-auto-create-suppression.patch

BuildArch:        noarch
BuildRequires:    python2-devel
BuildRequires:    python-setuptools
BuildRequires:    intltool

Requires(post):   systemd-units
Requires(preun):  systemd-units
Requires(postun): systemd-units
Requires(pre):    shadow-utils
Requires:         python-glance = %{version}-%{release}

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
Requires:         python-migrate
Requires:         python-paste-deploy
Requires:         python-routes
Requires:         python-sqlalchemy
Requires:         python-webob
Requires:         python-crypto
Requires:         pyxattr

%description -n   python-glance
OpenStack Image Service (code-named Glance) provides discovery, registration,
and delivery services for virtual disk images.

This package contains the glance Python library.

%package doc
Summary:          Documentation for OpenStack Image Service
Group:            Documentation

Requires:         %{name} = %{version}-%{release}

BuildRequires:    systemd-units
BuildRequires:    python-sphinx
BuildRequires:    graphviz

# Required to build module documents
BuildRequires:    python-boto
BuildRequires:    python-daemon
BuildRequires:    python-eventlet
BuildRequires:    python-gflags
BuildRequires:    python-routes
BuildRequires:    python-sqlalchemy
BuildRequires:    python-webob

%description      doc
OpenStack Image Service (code-named Glance) provides discovery, registration,
and delivery services for virtual disk images.

This package contains documentation files for glance.

%prep
%setup -q -n glance-%{version}

%patch0001 -p1
%patch0002 -p1
%patch0003 -p1
%patch0004 -p1
%patch0005 -p1
%patch0006 -p1
%patch0007 -p1

sed -i 's|\(sql_connection = \)sqlite:///glance.sqlite|\1mysql://glance:glance@localhost/glance|' etc/glance-registry.conf

sed -i '/\/usr\/bin\/env python/d' glance/common/config.py glance/registry/db/migrate_repo/manage.py

%build
%{__python} setup.py build

%install
%{__python} setup.py install -O1 --skip-build --root %{buildroot}

# Delete tests
rm -fr %{buildroot}%{python_sitelib}/tests

export PYTHONPATH="$( pwd ):$PYTHONPATH"
pushd doc
sphinx-build -b html source build/html
sphinx-build -b man source build/man

mkdir -p %{buildroot}%{_mandir}/man1
install -p -D -m 644 build/man/*.1 %{buildroot}%{_mandir}/man1/
popd

# Fix hidden-file-or-dir warnings
rm -fr doc/build/html/.doctrees doc/build/html/.buildinfo
rm -f %{buildroot}%{_sysconfdir}/glance*.conf
rm -f %{buildroot}%{_sysconfdir}/glance*.ini
rm -f %{buildroot}%{_sysconfdir}/logging.cnf.sample
rm -f %{buildroot}%{_sysconfdir}/policy.json
rm -f %{buildroot}/usr/share/doc/glance/README.rst

# Setup directories
install -d -m 755 %{buildroot}%{_sharedstatedir}/glance/images

# Config file
install -p -D -m 644 etc/glance-api.conf %{buildroot}%{_sysconfdir}/glance/glance-api.conf
install -p -D -m 644 etc/glance-api-paste.ini %{buildroot}%{_sysconfdir}/glance/glance-api-paste.ini
# glance-registry.conf contains a db password
install -p -D -m 640 etc/glance-registry.conf %{buildroot}%{_sysconfdir}/glance/glance-registry.conf
install -p -D -m 644 etc/glance-registry-paste.ini %{buildroot}%{_sysconfdir}/glance/glance-registry-paste.ini
install -p -D -m 644 etc/glance-cache.conf %{buildroot}%{_sysconfdir}/glance/glance-cache.conf
install -p -D -m 644 etc/glance-cache-paste.ini %{buildroot}%{_sysconfdir}/glance/glance-cache-paste.ini
install -p -D -m 644 etc/glance-scrubber.conf %{buildroot}%{_sysconfdir}/glance/glance-scrubber.conf
install -p -D -m 644 etc/glance-scrubber-paste.ini %{buildroot}%{_sysconfdir}/glance/glance-scrubber-paste.ini
install -p -D -m 644 etc/policy.json %{buildroot}%{_sysconfdir}/glance/policy.json

# Initscripts
install -p -D -m 644 %{SOURCE1} %{buildroot}%{_unitdir}/openstack-glance-api.service
install -p -D -m 644 %{SOURCE2} %{buildroot}%{_unitdir}/openstack-glance-registry.service

# Logrotate config
install -p -D -m 644 %{SOURCE3} %{buildroot}%{_sysconfdir}/logrotate.d/openstack-glance

# Install pid directory
install -d -m 755 %{buildroot}%{_localstatedir}/run/glance

# Install log directory
install -d -m 755 %{buildroot}%{_localstatedir}/log/glance

# Install database setup helper script.
install -p -D -m 755 %{SOURCE4} %{buildroot}%{_bindir}/openstack-glance-db-setup

%pre
getent group glance >/dev/null || groupadd -r glance -g 161
getent passwd glance >/dev/null || \
useradd -u 161 -r -g glance -d %{_sharedstatedir}/glance -s /sbin/nologin \
-c "OpenStack Glance Daemons" glance
exit 0

%post
if [ $1 -eq 1 ] ; then
    # Initial installation
    /bin/systemctl daemon-reload >/dev/null 2>&1 || :
fi


%preun
if [ $1 -eq 0 ] ; then
    # Package removal, not upgrade
    /bin/systemctl --no-reload disable openstack-glance-api.service > /dev/null 2>&1 || :
    /bin/systemctl --no-reload disable openstack-glance-registry.service > /dev/null 2>&1 || :
    /bin/systemctl stop openstack-glance-api.service > /dev/null 2>&1 || :
    /bin/systemctl stop openstack-glance-registry.service > /dev/null 2>&1 || :
fi

%postun
/bin/systemctl daemon-reload >/dev/null 2>&1 || :
if [ $1 -ge 1 ] ; then
    # Package upgrade, not uninstall
    /bin/systemctl try-restart openstack-glance-api.service >/dev/null 2>&1 || :
    /bin/systemctl try-restart openstack-glance-registry.service >/dev/null 2>&1 || :
fi

%files
%doc README.rst
%{_bindir}/glance
%{_bindir}/glance-api
%{_bindir}/glance-control
%{_bindir}/glance-manage
%{_bindir}/glance-registry
%{_bindir}/glance-cache-cleaner
%{_bindir}/glance-cache-manage
%{_bindir}/glance-cache-prefetcher
%{_bindir}/glance-cache-pruner
%{_bindir}/glance-scrubber
%{_bindir}/openstack-glance-db-setup
%{_unitdir}/openstack-glance-api.service
%{_unitdir}/openstack-glance-registry.service
%{_mandir}/man1/glance*.1.gz
%dir %{_sysconfdir}/glance
%config(noreplace) %attr(-, root, glance) %{_sysconfdir}/glance/glance-api.conf
%config(noreplace) %attr(-, root, glance) %{_sysconfdir}/glance/glance-api-paste.ini
%config(noreplace) %attr(-, root, glance) %{_sysconfdir}/glance/glance-registry.conf
%config(noreplace) %attr(-, root, glance) %{_sysconfdir}/glance/glance-registry-paste.ini
%config(noreplace) %attr(-, root, glance) %{_sysconfdir}/glance/glance-cache.conf
%config(noreplace) %attr(-, root, glance) %{_sysconfdir}/glance/glance-cache-paste.ini
%config(noreplace) %attr(-, root, glance) %{_sysconfdir}/glance/glance-scrubber.conf
%config(noreplace) %attr(-, root, glance) %{_sysconfdir}/glance/glance-scrubber-paste.ini
%config(noreplace) %attr(-, root, glance) %{_sysconfdir}/glance/policy.json
%config(noreplace) %attr(-, root, glance) %{_sysconfdir}/logrotate.d/openstack-glance
%dir %attr(0755, glance, nobody) %{_sharedstatedir}/glance
%dir %attr(0755, glance, nobody) %{_localstatedir}/log/glance
%dir %attr(0755, glance, nobody) %{_localstatedir}/run/glance

%files -n python-glance
%doc README.rst
%{python_sitelib}/glance
%{python_sitelib}/glance-%{version}-*.egg-info

%files doc
%doc doc/build/html

%changelog
* Mon May 21 2012 Pádraig Brady <P@draigBrady.com> - 2012.1-6
- Sync with essex stable

* Fri May 18 2012 Alan Pevec <apevec@redhat.com> - 2012.1-5
- Drop hard dep on python-kombu, notifications are configurable

* Wed Apr 25 2012 Pádraig Brady <P@draigBrady.com> - 2012.1-4
- Fix leak of swift objects on deletion

* Tue Apr 10 2012 Pádraig Brady <P@draigBrady.com> - 2012.1-3
- Fix db setup script to correctly start mysqld

* Tue Apr 10 2012 Pádraig Brady <P@draigBrady.com> - 2012.1-2
- Fix startup failure due to a file ownership issue (#811130)

* Mon Apr  9 2012 Pádraig Brady <P@draigBrady.com> - 2012.1-1
- Update to Essex final

* Fri Mar 30 2012 Russell Bryant <rbryant@redhat.com> - 2012.1-0.11.rc2
- Update to Essex rc2

* Wed Mar 28 2012 Russell Bryant <rbryant@redhat.com> - 2012.1-0.10.rc1
- Update openstack-glance-db-setup to common script from openstack-keystone package.
- Change permissions of glance-registry.conf to 0640.
- Set group on all config files to glance.

* Tue Mar 27 2012 Russell Bryant <rbryant@redhat.com> - 2012.1-0.9.rc1
- Use MySQL by default.
- Add openstack-glance-db-setup script.

* Wed Mar 21 2012 Russell Bryant <rbryant@redhat.com> - 2012.1-0.8.rc1
- Fix source URL for essex rc1

* Wed Mar 21 2012 Russell Bryant <rbryant@redhat.com> - 2012.1-0.7.rc1
- Update to essex rc1

* Thu Mar 8 2012 Dan Prince <dprince@redhat.com> - 2012.1-0.6.e4
- Include config files for cache and scrubber.

* Fri Mar 2 2012 Russell Bryant <rbryant@redhat.com> - 2012.1-0.5.e4
- Add python-iso8601 dependency.

* Fri Mar 2 2012 Russell Bryant <rbryant@redhat.com> - 2012.1-0.4.e4
- Update to essex-4 milestone.
- Change python-xattr depdendency to pyxattr.
- Add pysendfile dependency.

* Mon Feb 13 2012 Russell Bryant <rbryant@redhat.com> - 2012.1-0.3.e3
- Set PrivateTmp=true in glance systemd unit files. (rhbz#782505)
- Add dependency on python-crypto. (rhbz#789943)

* Mon Jan 30 2012 Russell Bryant <rbryant@redhat.com> - 2012.1-0.2.e3
- Update how patches are managed to use update_patches.sh script

* Thu Jan 26 2012 Russell Bryant <rbryant@redhat.com> - 2012.1-0.1.e3
- Update to essex-3 milestone

* Thu Jan 26 2012 Russell Bryant <rbryant@redhat.com> - 2011.3.1-2
- Add python-migrate dependency to python-glance (rhbz#784891)

* Fri Jan 20 2012 Pádraig Brady <P@draigBrady.com> - 2011.3.1-1
- Update to 2011.3.1 final

* Wed Jan 18 2012 Mark McLoughlin <markmc@redhat.com> - 2011.3.1-0.2.1063%{?dist}
- Update to latest 2011.3.1 release candidate

* Tue Jan 17 2012 Mark McLoughlin <markmc@redhat.com> - 2011.3.1-0.1.1062%{?dist}
- Update to 2011.3.1 release candidate
- Includes 6 new patches from upstream

* Fri Jan  6 2012 Mark McLoughlin <markmc@redhat.com> - 2011.3-4
- Rebase to latest upstream stable/diablo branch adding ~20 patches

* Tue Dec 20 2011 David Busby <oneiroi@fedoraproject.org> - 2011.3-3
- Depend on python-httplib2

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
