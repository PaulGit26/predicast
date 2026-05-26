# 📌 Instrucciones para Conectar con GitHub

Tu proyecto PREDICAST v4.0 ya está configurado con **Git localmente**. Sigue estos pasos para conectarlo con GitHub:

---

## 1️⃣ Crear Repositorio en GitHub

1. Ve a https://github.com/new
2. Ingresa el nombre: `predicast` (o el que prefieras)
3. Descripción: `Sistema Inteligente de Planificación de Demanda - Forecasting con XGBoost`
4. Selecciona **Private** (privado) o **Public** según prefieras
5. **NO** inicialices con README, .gitignore o licencia (ya los tenemos)
6. Click en **Create repository**

---

## 2️⃣ Conectar Remote a GitHub

Después de crear el repo, copia el comando que GitHub te muestra. Será algo como:

```bash
git remote add origin https://github.com/TU_USUARIO/predicast.git
```

Ejecuta en tu terminal:

```bash
cd d:\Desktop\Predicast\07_Sistema_Produccion

# Agregar el remote
git remote add origin https://github.com/TU_USUARIO/predicast.git

# Verificar que se agregó correctamente
git remote -v
```

Debería mostrar algo como:
```
origin  https://github.com/TU_USUARIO/predicast.git (fetch)
origin  https://github.com/TU_USUARIO/predicast.git (push)
```

---

## 3️⃣ Subir tu Proyecto a GitHub

```bash
# Cambiar rama master a main (opcional, pero recomendado)
git branch -m master main

# Subir los commits
git push -u origin main
```

Si todo funciona, verás algo como:
```
Enumerating objects: ...
Counting objects: 100%
...
 * [new branch]      main -> main
Branch 'main' set up to track remote branch 'main' from 'origin'.
```

---

## 4️⃣ Verificar en GitHub

1. Ve a tu repositorio en https://github.com/TU_USUARIO/predicast
2. Verifica que todos tus archivos estén ahí
3. Verifica que el README.md se vea formateado correctamente

---

## 5️⃣ Configurar SSH (Opcional pero Recomendado)

Para evitar escribir contraseña en cada push:

```bash
# Generar clave SSH (si no la tienes)
ssh-keygen -t ed25519 -C "tu_email@ejemplo.com"

# Copiar la clave pública
cat ~/.ssh/id_ed25519.pub
```

Luego:
1. Ve a GitHub → Settings → SSH and GPG keys
2. Click en **New SSH key**
3. Pega tu clave pública
4. Cambia tu remote a SSH:
   ```bash
   git remote set-url origin git@github.com:TU_USUARIO/predicast.git
   ```

---

## 📋 Workflow Futuro

### Para hacer cambios:

```bash
# 1. Crear rama
git checkout -b feature/nombre-del-cambio

# 2. Hacer cambios en tus archivos

# 3. Ver cambios
git status

# 4. Agregar cambios
git add .

# 5. Commit
git commit -m "type: descripción del cambio"

# 6. Subir a GitHub
git push origin feature/nombre-del-cambio

# 7. (Opcional) Crear Pull Request en GitHub
```

### Tipos de commit recomendados:
- `feat:` - Nueva funcionalidad
- `fix:` - Corrección de bug
- `docs:` - Cambios en documentación
- `refactor:` - Reorganización de código
- `test:` - Tests
- `chore:` - Cambios de configuración

**Ejemplo:**
```bash
git commit -m "feat: agregar algoritmo dinámico de producción"
git commit -m "fix: corregir cálculo de stock de seguridad"
git commit -m "docs: actualizar README con instrucciones"
```

---

## 🔄 Ver Historial

```bash
# Ver commits
git log --oneline

# Ver cambios específicos
git show <commit-hash>

# Ver ramas
git branch -a
```

---

## 🆘 Troubleshooting

**Error: "fatal: No commits yet"**
- Ya resuelto: ya tenemos commits

**Error: "fatal: not a git repository"**
- Asegúrate de estar en el directorio correcto: `d:\Desktop\Predicast\07_Sistema_Produccion`

**Error: "Connection refused" o "Authentication failed"**
- Verifica tu contraseña de GitHub
- Considera usar SSH en lugar de HTTPS

**Quiero resetear todo y empezar de nuevo:**
```bash
# Eliminar remote
git remote remove origin

# Volver a agregar
git remote add origin https://github.com/TU_USUARIO/predicast.git

# Subir como si fuera la primera vez
git push -u origin main
```

---

## ✅ Verificar Configuración

```bash
# Ver configuración git
git config --list

# Ver remotes configurados
git remote -v

# Ver rama actual
git branch

# Ver estado actual
git status
```

---

## 💡 Tips Útiles

1. **Update local** antes de empezar:
   ```bash
   git pull origin main
   ```

2. **Crear `.gitattributes`** para evitar problemas de CRLF:
   ```bash
   echo "* text=auto" > .gitattributes
   git add .gitattributes
   git commit -m "chore: agregar .gitattributes"
   ```

3. **Proteger rama main** en GitHub:
   - Ir a Settings → Branches
   - Click en "Add rule"
   - Seleccionar "main"
   - Activar "Require pull request reviews before merging"

---

## 📚 Recursos Útiles

- [Git Documentation](https://git-scm.com/doc)
- [GitHub Guides](https://guides.github.com/)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [GitHub Markdown](https://docs.github.com/en/github/writing-on-github)

---

**¡Listo!** Tu proyecto ahora está versionado con Git y listo para conectar con GitHub. 🚀
