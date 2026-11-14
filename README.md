# Glitching Realities

Proyecto de Unreal Engine 5.8.4 basado en la plantilla Third Person (Blueprint).
Protagonista: un gato glitcheado.

## Versión del motor: Unreal Engine 5.8.4

Todo el equipo debe usar **UE 5.8.4** (la versión del Epic Games Launcher). Los assets guardados con una versión más nueva no abren en una más vieja.

1. En el Epic Games Launcher → Unreal Engine → Biblioteca, revisa que la 5.8 diga **5.8.4**. Si no, actualízala.
2. Abre `Glitching_Realities.uproject`. Si Windows pregunta qué versión usar, elige la **5.8**.
3. No uses "Switch Unreal Engine version" ni builds compiladas desde código: cambian `EngineAssociation` en el `.uproject` por un GUID local y le rompen el proyecto a los demás. Debe quedar siempre `"EngineAssociation": "5.8"`.

Para confirmarla: Help → About Unreal Editor tiene que decir 5.8.4.

## Git LFS

Los assets binarios usan Git LFS: ejecuta `git lfs install` antes de clonar.

## Perfil gráfico

El proyecto está configurado ligero (sin Lumen, ray tracing, Nanite ni sombras virtuales) para que corra en gráficos integrados. No lo reactiven sin avisar al equipo.
