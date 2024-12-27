import os
import subprocess
import socket

def run_command(command):
    """Ejecuta un comando en la terminal y muestra la salida."""
    result = subprocess.run(command, shell=True, text=True, capture_output=True)
    if result.returncode != 0:
        raise Exception(f"Error ejecutando el comando: {command}\n{result.stderr}")
    print(result.stdout)

def add_user(username):
    """Creación de usuario"""
    print(f"Creando usuario {username}.")
    run_command(f"adduser --disabled-password --gecos '' {username}")
    run_command(f"chmod 777 /home/{username}")

def setup_virtualenv(username):
    """Creando el entorno virtual"""
    print("Creando el entorno virtual")
    run_command(f"sudo -H -u {username} bash -c 'cd /home/{username}/ && python3 -m venv venv && source venv/bin/activate'")

def git_and_project(username):
    """Instala git y configura el proyecto."""
    print("Instalando git")
    run_command("apt install git -y")
    print("Clonando el proyecto del repositorio.")
    run_command(f"sudo -H -u {username} bash -c 'cd /home/{username}/ && git clone https://github.com/xXJuanDavidXx/Sistema-de-compra-venta-e-inventario..git'")

def install_requirements(username):
    print("Instalando requerimientos.")
    run_command(f"sudo -H -u {username} bash -c 'cd /home/{username}/ && source venv/bin/activate && pip install -r Sistema-de-compra-venta-e-inventario./requirements.txt'")

def install_supervisor():
    """Instala y inicia supervisor"""
    print("Instalando y iniciando supervisor")
    run_command("apt install supervisor -y")
    run_command("systemctl enable supervisor && systemctl start supervisor")

def configure_supervisor(username):
    """Configurando supervisor para ejecutar uvicorn"""
    print("Configurando supervisor para ejecutar uvicorn.")
    conf = f"""
[program:uvicorn] 
command=/home/{username}/venv/bin/uvicorn Colores.asgi:application --host 127.0.0.1 --port 8000 --log-level info 
directory=/home/{username}/Sistema-de-compra-venta-e-inventario.
user={username}
autostart=true 
autorestart=true 
stdout_logfile=/home/{username}/uvicorn.log 
stderr_logfile=/home/{username}/uvicorn_error.log 
process_name=%(program_name)s_%(process_num)02d
"""
    with open("/etc/supervisor/conf.d/uvicorn.conf", "w") as file:
        file.write(conf)

    run_command("systemctl restart supervisor")

    print("Comprobando el servidor.\n")
    run_command(f"cat /home/{username}/uvicorn_error.log")

def install_nginx():
    """Instala Nginx."""
    print("Instalando Nginx...")
    run_command("apt install nginx -y")

###Probado hasta aquí funciona correctamente.

    run_command("systemctl start nginx")
    run_command("systemctl enable nginx")

def config_nginx(username,ip):
    """Configurando nginx"""
    print("Configurando nginx")
    conf = f"""
server {{
    listen 80;
    server_name {ip};

    location = /favicon.ico {{ access_log off; log_not_found off; }}
    
    location /static/ {{ 
        root /home/{username}/Sistema-de-compra-venta-e-inventario.; 
    }}  

    location /media/ {{ 
        root /home/{username}/Sistema-de-compra-venta-e-inventario.;
    }}

    location / {{
        proxy_pass http://127.0.1.1:8000; 
        proxy_set_header Host $host; 
        proxy_set_header X-Real-IP $remote_addr; 
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }}
}}
"""
    with open(f"/etc/nginx/sites-available/{ip}", "w") as nginx:
        nginx.write(conf)
          
    run_command(f"ln -s /etc/nginx/sites-available/{ip} /etc/nginx/sites-enabled/") 
    run_command("systemctl restart nginx")

def configure_firewall():
    """Configura el firewall usando UFW."""
    print("Configurando el firewall...")
    run_command("apt install ufw -y")
    run_command("ufw allow 'Nginx Full'")
    run_command("ufw allow OpenSSH")
    run_command("ufw enable")

def get_private_ip():
    """Obtiene la IP privada del servidor."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip_address = s.getsockname()[0]
    except Exception as e:
        print(f"Error al obtener la IP privada: {e}")
        ip_address = None
    finally:
        s.close()
    return ip_address

def main():
    """Configura un servidor web completo."""
    nombre = "webadmin"
    add_user(nombre)
    setup_virtualenv(nombre)
    git_and_project(nombre)
    install_requirements(nombre)
    install_supervisor()
    configure_supervisor(nombre)
    install_nginx()
    
    ip = get_private_ip()
    if ip:
        config_nginx(nombre,ip)
    configure_firewall()
    
    print("Configuración completada. Tu servidor web está listo y funcionando.")

if __name__ == "__main__":
    main()

