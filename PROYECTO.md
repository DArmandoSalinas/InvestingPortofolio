# Plataforma de inversión con IA

## Visión
Plataforma web privada multiusuario para decidir dónde invertir: ranking de
empresas de EE. UU. y México, señales de corto plazo (acciones de EE. UU. y
crypto), perfil de inversionista y portafolio. Grok (API de xAI) actúa como
analista. Acceso solo por invitación. La plataforma NO ejecuta operaciones.

## Prioridades (en este orden)
1. Ranking y análisis de empresas (pantalla principal)
2. Señales de corto plazo
3. Dónde invertir según mi perfil
4. Portafolio

## Stack
- Frontend: Next.js (App Router) + TypeScript + Tailwind + Framer Motion
- Solo escritorio: diseñado para pantallas de 1280px en adelante
- Gráficas: TradingView Lightweight Charts (velas), Recharts (resto)
- Backend: Python + FastAPI
- Base de datos y autenticación: Supabase (PostgreSQL + Auth + Row Level Security)
- Datos: yfinance (EE. UU. y BMV con sufijo .MX), Finnhub (noticias y
  fundamentales), CoinGecko/Binance (crypto)
- Indicadores: se calculan en código. La media de 200 días es el promedio
  simple de los últimos 200 cierres ajustados; no se toma de Yahoo.
- IA: API de xAI (Grok), solo para interpretar datos ya calculados
- Tareas programadas: en el servidor del backend (corren 24/7)
- Hosting: Vercel (frontend), Railway o Render (backend)
- Notificaciones: Web Push del navegador
- Llaves de API en variables de entorno, nunca en el código

## Usuarios y acceso
- Plataforma privada multiusuario, acceso solo por invitación
- Inicio de sesión con correo y Google
- Roles: administrador (yo) y miembro
- Compartido entre todos: ranking, señales, análisis y resumen matutino
  (se generan una vez al día para todos)
- Privado por usuario: perfil, portafolio, historial personal y
  preferencias de notificación
- Aviso visible: contenido informativo, no es asesoría financiera

## Sistema de diseño (inspiración: Apple, Tesla, SpaceX)
- Fondo negro (#000), superficies #0a0a0a y #141414
- Tipografía Inter, títulos grandes y ligeros, mucho espacio negativo
- Números con tabular-nums
- Un solo color de acento; verde y rojo suaves solo para subidas y bajadas
- Bordes de 1px (blanco al 8%), esquinas redondeadas grandes
- Layouts de varias columnas aprovechando pantallas anchas
- Animaciones suaves: aparición escalonada, números que cuentan, transiciones
- Elegancia por lo que se quita: menos elementos, más claridad

## Módulo 1: Ranking de empresas
- Universo inicial: S&P 500 y emisoras principales de la BMV
- Tres puntuaciones de 0 a 100:
  - Crecimiento: crecimiento de ingresos y utilidades
  - Valor: P/E, P/S y EV/EBITDA comparados contra su sector
  - Momentum: rendimiento a 3, 6 y 12 meses; precio vs. media de 200 días
- Puntuación general y filtros por estilo, mercado y sector
- Resaltar empresas con puntuación alta en los tres estilos
- Si faltan datos, marcarlo claramente; nunca rellenarlos
- Ficha de empresa: gráfica de velas, métricas clave, explicación de cada
  calificación, cifras del último reporte trimestral (ingresos, utilidad y
  variación contra el mismo trimestre del año anterior) y resumen de Grok.
  Si la fuente no trae el reporte, la ficha lo dice y no inventa cifras.

## Módulo 2: Señales de corto plazo
- Activos: acciones de EE. UU. y crypto
- Señales generadas por reglas en código; Grok aporta contexto y noticias
- Cada señal: entrada, stop-loss, objetivo, confianza, razones y riesgos
- Registrar TODAS las señales y evaluarlas automáticamente después,
  descontando comisiones configurables. La lista inicial son quince
  acciones líquidas de EE. UU. más Bitcoin y Ethereum; el administrador la
  edita en Seguimiento. Comisión de ida y vuelta al arranque: 0,10% en
  acciones y 0,20% en crypto. Horizonte al arranque: 10 sesiones. Un cambio
  de comisión u horizonte solo aplica a señales nuevas. Si el
  stop y el objetivo caen el mismo día, cuenta el stop. La vela del día en
  curso no se usa: una acción cuenta cuando cerró Nueva York (16:00) y crypto
  cuando cerró el día UTC.

## Módulo 3: Mi perfil y dónde invertir
- Cuestionario: monto, aportación mensual, plazo, meta, tolerancia al riesgo.
  El perfil es de cada usuario.
- Comparador de cinco casilleros: CETES, ahorro, ETFs, acciones y crypto.
  Un rendimiento solo se muestra si sale de precios ya cerrados, con las
  fechas reales. La tasa de CETES no se inventa: si no hay una fuente
  cargada, el casillero queda sin tasa.
- La mezcla de Grok son enteros que suman 100. Si no suma 100, no se
  muestra. No es una instrucción de compra o venta.

## Módulo 4: Portafolio
- Registro manual, por usuario, de posiciones y su evolución.
- CETES y ahorro se quedan al monto registrado: no tienen precio de mercado.
- Si a una posición con mercado le falta el precio, no se guarda como cero
  y el total de esa moneda no se calcula.

## Módulo 5: Historial
- Marcador de señales en `/historial`: aciertos, rendimiento neto de
  comisiones y comparación contra comprar y mantener el S&P 500 y BTC.
- Solo entran señales cerradas. Si ninguna ha cerrado, la pantalla lo dice
  y no inventa un porcentaje. Un rendimiento que falte no se cuenta como cero.

## Resumen matutino
- Se genera todos los días a las 9:00 de Nueva York, también en fin de
  semana. Esa hora ya cae en Monterrey: 7:00 mientras EE. UU. tiene horario
  de verano y 8:00 cuando no. México no cambia el reloj.
- Contenido: cambios en el ranking, señales del día, noticias y eventos clave
- Llega como notificación, como correo a quienes están activos en Acceso, y
  abre una pantalla de resumen

## Reglas para Grok
- Usar solo los datos proporcionados más sentimiento reciente en X
- Nunca inventar cifras
- "Sin operación" es una respuesta válida
- Responder siempre en JSON con estructura fija

## Configuración (administrador)
- Comisiones y horizonte en `/admin/seguimiento`, entre 0% y 5% y de 1 a 30
  sesiones. La lista de seguimiento se pausa o se reactiva; no se borra una
  señal abierta al pausar su activo.
- Gestión de invitaciones y usuarios en Acceso. Al agregar un correo se
  envía el enlace de entrada. Con SMTP sale a la bandeja real; sin SMTP, en
  esta computadora queda en la bandeja local.

## Fases de construcción
1. Estructura, autenticación con Supabase, sistema de diseño y pantalla de
   Ranking con datos de ejemplo sobre el esquema real
2. Datos reales y cálculo de puntuaciones
3. Ficha de empresa e integración con Grok
4. Señales de corto plazo y evaluación automática
5. Resumen matutino y notificaciones
6. Perfil, comparador y portafolio
7. Despliegue en producción (Vercel + Railway/Render) e invitaciones

## Decisiones cerradas

Estas decisiones fijan la Fase 1 y el esquema. No se reabren al implementar
las fases siguientes, salvo un cambio explícito de este documento.

### Frontera de datos
- El navegador usa Supabase solo para la sesión y el perfil.
- FastAPI es el dueño del ranking, los snapshots y la lista blanca. Escribe
  con la service role. El cliente no lee ni escribe esas tablas.
- Monorepo: `apps/web` (Next.js) y `apps/api` (FastAPI). Migraciones en
  `supabase/`.

### Acceso
- Tabla `allowed_emails`: correo en minúsculas, rol `admin` o `member`,
  activo.
- Inicio de sesión con enlace mágico al correo y con Google. Google funciona
  cuando existen las credenciales; no bloquea el desarrollo local.
- Un trigger rechaza el alta si el correo no está activo en la lista.
- `ADMIN_EMAIL` es el administrador de arranque: la API lo vuelve a dejar
  activo al iniciar. No se puede revocar desde la pantalla.
- Revocar a otra persona pone `active = false` en la lista y en su perfil.
  La siguiente petición cierra la sesión.
- La Fase 1 incluye la pantalla Acceso (alta, rol, revocación). No incluye
  comisiones ni edición del universo.

### Universo e identidad
- Universo: S&P 500 (tabla de Wikipedia) e IPC (tabla de componentes de
  Wikipedia). El IPC se ajusta con los rebalanceos de 2026: salen CUERVO
  (marzo) y TLEVISA CPO (septiembre) y entra ALPEK A. Si la tabla ya trae
  el cambio, no se duplica. El esquema guarda `universe_source` (`sp500` o
  `ipc`). La pantalla para editar la lista no entra todavía.
- Cada emisora tiene `id` interno y es única por `(market, symbol)`.
  `symbol` no lleva sufijo (`AAPL`, `WALMEX`). `yahoo_symbol` guarda la forma
  de Yahoo (`WALMEX.MX`, `BRK-B`) para la Fase 2.
- `market` es `us` o `mx`. Moneda `USD` o `MXN`, guardada en la empresa.
- Sector GICS de 11, código estable en la base y nombre en español en la
  interfaz.

### Puntuaciones
- `score_snapshots` no reescribe fechas anteriores. `as_of` se interpreta
  en `America/Monterrey`. Volver a calcular el mismo día reemplaza esa fecha.
  `calculated` distingue el fixture de un día calculado.
- Crecimiento, valor y momentum van de 0 a 100 o son nulos. La general es el
  promedio simple, redondeado al entero más cercano con .5 hacia arriba, solo
  si las tres existen. Si falta una, la general es nula.
- Missing y not applicable son distintos. Missing: el dato debía existir.
  Not applicable: P/E cuando las utilidades no son positivas; EV/EBITDA en
  el sector `financials`. El score usa los insumos que sí aplican. Queda nulo
  solo si no quedó ninguno.
- Un hueco no se guarda como cero.
- Valor: percentil dentro del mismo mercado y
  sector GICS, invertido (más barato, puntaje más alto), si hay al menos 8
  emisoras. Si el sector en México no llega a 8, se compara contra ese sector
  del S&P 500 y se guarda `value_reference = sp500_sector` para mostrarlo.
  Si el grupo local sí alcanza, los mercados no se mezclan. No se inventa el
  múltiplo.
- Crecimiento: crecimiento anual de ingresos y de utilidades. Escala
  lineal recortada: −20% = 0, 0% = 50, +30% = 100. Promedio de los que existan.
- Momentum: rendimientos de 63, 126 y 252 sesiones (cerca de 3, 6 y 12
  meses) con −30% = 0, 0% = 50, +40% = 100. Precio / media de 200 cierres
  ajustados: 0.70 = 0, 1.00 = 50, 1.30 = 100. Peso igual entre los que
  existan. Si no hay historia suficiente, el dato falta; no se guarda cero.
- El estilo no es una etiqueta de la empresa. El filtro reordena por esa
  puntuación y puede exigir un mínimo. Mercado y sector sí filtran.
- Alta en los tres: las tres puntuaciones en `RANK_HIGHLIGHT_MIN` o más
  (default 70) el mismo día. Si una es nula, no entra.

### Interfaz
- Español (es-MX). Solo escritorio, desde 1280px. Por debajo, un aviso y no
  hay layout móvil.
- Acento `#f5f5f7`. Verde y rojo quedan reservados para subidas y bajadas.
  Las puntuaciones no se pintan como compra o venta.
- La tabla es densa. El bloque de altas en los tres va arriba y es corto.
  Una fila abre la ficha. La ficha muestra las velas del último año y explica
  las tres puntuaciones con los datos ya guardados. Grok redacta una lectura
  con esos datos y con publicaciones recientes de X. No inventa cifras. La
  llave va en `.env` como `GrokAI` o `XAI_API_KEY`, y no se escribe en el código.
- Aviso persistente: el contenido es informativo, no es asesoría financiera
  y la plataforma no ejecuta operaciones.
- El fixture de la Fase 1 son 25 emisoras con puntajes escritos a mano, con
  fecha `2026-10-02` y `calculated = false`. Si el día más reciente no está
  calculado, la pantalla dice «Datos de ejemplo». Un día calculado dice
  «Calculado».

## Desarrollo local
- Frontend: `npm run dev` en la raíz (Next.js en el puerto 3000).
- API: `npm run dev:api` (FastAPI en el puerto 8000).
- Base: Supabase local (`npx supabase start`), que requiere Docker.
- Copia `apps/web/.env.example` a `apps/web/.env.local` y `apps/api/.env.example`
  a `apps/api/.env`. El enlace de correo se lee en Mailpit
  (http://127.0.0.1:54324).
- Ranking calculado: mientras la API está encendida, revisa cada 30 minutos
  si el día de Monterrey ya tiene snapshot calculado. Si no, lo calcula y lo
  guarda. En el mismo ciclo genera las señales nuevas y cierra las que ya
  tocaron stop, objetivo o el plazo de 10 sesiones. Desde las 9:00 de Nueva
  York, todos los días, publica el resumen si todavía no existe y lo envía
  por correo a los accesos activos.
  `npm run refresh` recalcula
  el ranking a mano. `npm run refresh -- --limit 3` prueba el cálculo y no
  escribe la base.
