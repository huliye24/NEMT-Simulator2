# NEMT Simulator - Project Configuration

# Go Configuration
go.workspace=src/

# Python Configuration
python.default.venv.path=src/nemt-os/.venv
python.default.venv.name=nemt-os-venv

# JavaScript/TypeScript
javascript.suggest.autoImports=true
javascript.validate.all=false
typescript.validate.all=false

# Framework
javascript.frameworks.react=true
typescript.tsdk=src/web/node_modules/typescript/lib

# Electron
electron.app.paths.main=src/desktop/main
electron.app.paths.preload=src/desktop/preload

# Build
build.tools.make.path=make
build.tools.go.path=go

# Directories
directories.project=.
directories.module=src
