Vagrant.configure('2') do |config|
  customize = [
    'modifyvm', :id,
    '--cpus', ENV['BUILD_CPUS'] || '4',
    '--memory', ENV['BUILD_MEMORY'] || 1024,
  ]

  config.vm.box = 'fedora-22'
  config.vm.box_url = 'https://download.fedoraproject.org/pub/fedora/linux/releases/22/Cloud/x86_64/Images/Fedora-Cloud-Base-Vagrant-22-20150521.x86_64.vagrant-virtualbox.box'

  config.vm.provider :virtualbox do |v|
    v.customize customize
  end

  config.vm.provision :shell, inline: <<-eof
    test -f /usr/local/bin/brpm && exit

    set -o errexit

    yum install -y \
      createrepo \
      curl \
      fedora-packager \
      mock \
      python-pip

    usermod -G mock vagrant

    pip install ops

    echo -n "#!/usr/bin/env bash\n\nexec python /vagrant/brpm.py" > /usr/local/bin/brpm

    chmod 755 /usr/local/bin/brpm
  eof
end
