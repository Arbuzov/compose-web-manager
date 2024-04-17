from setuptools import setup

setup(
    name="compose-web-manager",
    version="1.0.0",
    maintainer="Serge Arbuzov",
    author_email="serge.arbuzov@spacebridge.com",
    maintainer_email="serge.arbuzov@spacebridge.com",
    description="Web interface to manage docker compose",
    long_description="Package provides web interface to manage spacebridge docker compose",
    url="https://spacebridge.com",
    package_dir={"": "src"},
    packages=["compose_web_manager"],
    include_package_data=True,
    data_files=[
        ("/lib/systemd/system", ["config/compose-web-manager.service"]),
        ("/etc/rsyslog.d/", ["config/16-sbc-compose-manager-backend.conf"]),
        ("/etc/spacebridge/compose-manager/", ["config/swagger.v1.yaml"]),
    ],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Framework :: aiohttp",
        "License :: Other/Proprietary License",
        "Natural Language :: English",
        "Operating System :: POSIX :: Linux",
    ],
    install_requires=[
        "aiohttp_cors==0.7.0",
        "aiohttp_session==2.9.0",
        "aiohttp_swagger==1.0.9",
        "aiohttp==3.6.3",
        "chardet==3.0.4",
        "idna==3.3",
        "cryptography",
        "decorator",
        "jsonschema",
        "jinja2==2.11.3",
    ],
    entry_points={"console_scripts": ["compose-web-manager=compose_web_manager:main"]},
    project_urls={
        "Source": "https://gitlab.asatnet.net/asat3/basic-sbc/web-manager-backend-python"
    },
    python_requires=">=3.5.1",
)
