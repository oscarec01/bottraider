# 📤 Guía para Subir a GitHub

## 1️⃣ Crear Repositorio en GitHub

1. Ve a https://github.com/new
2. Nombre del repositorio: `deriv-trading-bot` (o el que prefieras)
3. Descripción: "AI-powered trading bot for Deriv Synthetic Indices"
4. **NO** inicialices con README, .gitignore o licencia (ya los tienes)
5. Click en "Create repository"

## 2️⃣ Conectar y Subir

GitHub te mostrará comandos. Usa estos:

```bash
# Conectar tu repositorio local con GitHub
git remote add origin https://github.com/WilliamBismma/BotTrader.git

# Cambiar a rama main (opcional)
git branch -M main

# Subir tu código
git push -u origin main
```

## 3️⃣ Comandos Completos (Copiar y Pegar)

Reemplaza `TU_USUARIO` con tu nombre de usuario de GitHub:

```powershell
cd e:\Documentos\VS_desarrollos\python\bot_trader

git remote add origin https://github.com/WilliamBismma/BotTrader.git
git branch -M main
git push -u origin main
```

## 4️⃣ Autenticación

Si GitHub pide credenciales:

### Opción A: Token Personal (Recomendado)
1. Ve a GitHub → Settings → Developer settings → Personal access tokens
2. Generate new token (classic)
3. Selecciona scope: `repo`
4. Copia el token
5. Úsalo como contraseña cuando git lo pida

### Opción B: GitHub CLI
```bash
# Instalar GitHub CLI
winget install --id GitHub.cli

# Login
gh auth login

# Push
git push -u origin main
```

## 5️⃣ Verificar

Una vez subido, ve a:
```
https://github.com/TU_USUARIO/deriv-trading-bot
```

Deberías ver todos tus archivos excepto:
- ❌ config.py (protegido - tiene tus credenciales)
- ❌ *.xlsx (archivos de trading history)
- ❌ *.log (archivos de log)
- ❌ venv/ (entorno virtual)

## 6️⃣ Actualizaciones Futuras

```bash
# Ver cambios
git status

# Agregar todos los cambios
git add .

# Hacer commit
git commit -m "Descripción de tus cambios"

# Subir a GitHub
git push
```

## ⚠️ Importante

✅ **NUNCA** subas `config.py` - contiene tus credenciales
✅ Usa `config.example.py` como plantilla para otros usuarios
✅ Revisa que `.gitignore` esté funcionando antes de hacer push

## 🎯 Tu README.md está listo

El archivo README.md que creé incluye:
- ✅ Descripción del proyecto
- ✅ Instrucciones de instalación
- ✅ Guía de uso
- ✅ Documentación de estrategia
- ✅ Solución de problemas
- ✅ Disclaimer legal

¡Todo listo para hacerte famoso en GitHub! 🚀
