%if 0%{?rhel} && 0%{?rhel} <= 6
%{!?__python2: %global __python2 /usr/bin/python2}
%{!?python2_sitelib: %global python2_sitelib %(%{__python2} -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())")}
%{!?python2_sitearch: %global python2_sitearch %(%{__python2} -c "from distutils.sysconfig import get_python_lib; print(get_python_lib(1))")}
%endif

%global _pkg_name replugin
%global _src_name reworkerjuicer

Name: re-worker-juicer
Summary: RE RPM package propagation worker
Version: 0.0.1
Release: 1%{?dist}

Group: Applications/System
License: AGPLv3
Source0: %{_src_name}-%{version}.tar.gz
Url: https://github.com/rhinception/re-worker-juicer

BuildArch: noarch
BuildRequires: python2-devel, python-setuptools
Requires: reworker, juicer

%description
The Juicer worker worker allows you to upload and promote batches of RPMs
into Yum repositories. In juicer terminology, these batches of RPMs are
referred to as release carts.

%prep
%setup -q -n %{_src_name}-%{version}

%build
%{__python2} setup.py build

%install
%{__python2} setup.py install -O1 --root=$RPM_BUILD_ROOT --record=re-worker-juicer-files.txt

%files -f re-worker-juicer-files.txt
%doc README.md LICENSE AUTHORS
%dir %{python2_sitelib}/%{_pkg_name}

%changelog
* Thu Jun  5 2014 Steve Milner <stevem@gnulinux.et> - 0.0.1-1
- First release
