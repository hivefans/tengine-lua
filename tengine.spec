%define nginx_user      nginx
%define nginx_group     %{nginx_user}
%define nginx_home      %{_localstatedir}/lib/nginx
%define nginx_home_tmp  %{nginx_home}/tmp
%define nginx_logdir    %{_localstatedir}/log/nginx
%define nginx_confdir   %{_sysconfdir}/nginx
%define nginx_datadir   %{_datadir}/nginx
%define nginx_webroot   %{nginx_datadir}/html

Name:           tengine
Version:        2.0.3
Release:        3%{?dist}
Summary:        Robust, small and high performance HTTP and reverse proxy server
Group:          System Environment/Daemons

# BSD License (two clause)
# http://www.freebsd.org/copyright/freebsd-license.html
License:        BSD
URL:            http://tengine.taobao.org/
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

BuildRequires:      pcre-devel,zlib-devel
Requires:           pcre,openssl
# for /usr/sbin/useradd
Requires(pre):      shadow-utils
# for /sbin/service
Provides:           webserver

Source0:            tengine-%{version}.tar.gz
Source1:            ngx_devel_kit-0.2.18.tar.gz
Source2:            lua-nginx-module-0.9.12.tar.gz

# removes -Werror in upstream build scripts.  -Werror conflicts with
# -D_FORTIFY_SOURCE=2 causing warnings to turn into errors.

%description
Nginx [engine x] is an HTTP(S) server, HTTP(S) reverse proxy and IMAP/POP3
proxy server written by Igor Sysoev.
%prep
%setup -q -a1 -a2

%build
export LUAJIT_LIB=%{_libdir}
export LUAJIT_INC=%{_includedir}/luajit-2.0
# nginx does not utilize a standard configure script.  It has its own
# and the standard configure options cause the nginx configure script
# to error out.  This is is also the reason for the DESTDIR environment
# variable.  The configure script(s) have been patched (Patch1 and
# Patch2) in order to support installing into a build environment.
export DESTDIR=%{buildroot}
./configure \
     --prefix=%{nginx_datadir} \
     --sbin-path=%{_sbindir}/%{name} \
     --conf-path=%{nginx_confdir}/%{name}.conf \
     --user=nginx \
     --group=nginx \
     --add-module=lua-nginx-module-0.9.12 \
     --add-module=ngx_devel_kit-0.2.18
make %{?_smp_mflags}

%install
rm -rf %{buildroot}
make install DESTDIR=%{buildroot} INSTALLDIRS=vendor
find %{buildroot} -type f -name .packlist -exec rm -f {} \;
find %{buildroot} -type f -empty -exec rm -f {} \;
find %{buildroot} -type f -exec chmod 0644 {} \;
find %{buildroot} -type f -name '*.so' -exec chmod 0755 {} \;
chmod 0755 %{buildroot}%{_sbindir}/%{name}
%{__install} -p -d -m 0755 %{buildroot}%{nginx_confdir}/conf.d

%{__install} -p -d -m 0755 %{buildroot}%{nginx_home_tmp}
%{__install} -p -d -m 0755 %{buildroot}%{nginx_logdir}
%{__install} -p -d -m 0755 %{buildroot}%{nginx_webroot}

# convert to UTF-8 all files that give warnings.
for textfile in CHANGES
do
    mv $textfile $textfile.old
    iconv --from-code ISO8859-1 --to-code UTF-8 --output $textfile $textfile.old
    rm -f $textfile.old
done

%post
echo "
worker_processes  4;

events {
    worker_connections  1024;
}

http {
    include       mime.types;
    default_type  application/octet-stream;

    sendfile                  on;
    keepalive_timeout         3600;
    client_max_body_size      1024G;

    fastcgi_request_buffering off;
    fastcgi_connect_timeout   3600;
    fastcgi_read_timeout      3600;
    fastcgi_send_timeout      3600;

    server {
           listen 80;
        server_name localhost;

        location / {
            fastcgi_pass   localhost:8000;

            fastcgi_param   SCRIPT_NAME             \$fastcgi_script_name;
            fastcgi_param   REQUEST_METHOD          \$request_method;
            fastcgi_param   CONTENT_LENGTH          \$content_length;
            fastcgi_param   HTTP_RANGE              \$http_range;
            fastcgi_param   DOCUMENT_URI            \$document_uri;
            fastcgi_param   REQUEST_URI             \$request_uri;
            fastcgi_param   FORCE                   \$http_FORCE;
        }
    }
}" > ${buildroot}%{nginx_confdir}/%{name}.conf

%clean
rm -rf %{buildroot}

%pre
if [ $1 == 1 ]; then
    %{_sbindir}/useradd -c "Nginx user" -s /bin/false -r -d %{nginx_home} %{nginx_user} 2>/dev/null || :
fi

%files
%defattr(-,root,root,-)
%doc LICENSE CHANGES README
%{nginx_datadir}/
%{_sbindir}/%{name}
%dir %{nginx_confdir}
%dir %{nginx_confdir}/conf.d
%dir %{nginx_logdir}
%config(noreplace) %{nginx_confdir}/win-utf
%config(noreplace) %{nginx_confdir}/mime.types.default
%config(noreplace) %{nginx_confdir}/fastcgi.conf
%config(noreplace) %{nginx_confdir}/browsers
%config(noreplace) %{nginx_confdir}/module_stubs
%config(noreplace) %{nginx_confdir}/nginx.conf.default
%config(noreplace) %{nginx_confdir}/fastcgi.conf.default
%config(noreplace) %{nginx_confdir}/fastcgi_params
%config(noreplace) %{nginx_confdir}/fastcgi_params.default
%config(noreplace) %{nginx_confdir}/scgi_params
%config(noreplace) %{nginx_confdir}/scgi_params.default
%config(noreplace) %{nginx_confdir}/uwsgi_params
%config(noreplace) %{nginx_confdir}/uwsgi_params.default
%config(noreplace) %{nginx_confdir}/koi-win
%config(noreplace) %{nginx_confdir}/koi-utf
%config(noreplace) %{nginx_confdir}/%{name}.conf
%config(noreplace) %{nginx_confdir}/mime.types
%attr(-,%{nginx_user},%{nginx_group}) %dir %{nginx_home}
%attr(-,%{nginx_user},%{nginx_group}) %dir %{nginx_home_tmp}

