/*
 * AirplaneMode Doom: browser glue for PrBoom+ (GPL-2.0-or-later, like PrBoom+ itself).
 *
 * The page's touch controls call these instead of faking DOM keyboard events, so input
 * doesn't depend on how SDL reads the keyboard in a given browser.
 */
#ifdef __EMSCRIPTEN__
#include "doomdef.h"
#include "doomstat.h"
#include "d_event.h"
#include "d_main.h"
#include "m_misc.h"

/* after the Doom headers: em_js.h defines true/false, which doomtype.h declares as an enum */
#include <emscripten.h>

extern int messageToPrint;
extern dboolean messageNeedsInput;

/* A key went down (down=1) or up (down=0). key is a Doom key code (doomdef.h KEYD_*,
 * or a lower-case ASCII character). */
EMSCRIPTEN_KEEPALIVE void am_key(int down, int key)
{
  event_t ev = {0};
  ev.type = down ? ev_keydown : ev_keyup;
  ev.data1 = key;
  D_PostEvent(&ev);
}

/* Relative mouse movement: the touch "look" area turns the player with this. */
EMSCRIPTEN_KEEPALIVE void am_mouse(int dx, int dy)
{
  event_t ev = {0};
  ev.type = ev_mousemotion;
  ev.data2 = dx;
  ev.data3 = dy;
  D_PostEvent(&ev);
}

/* What's on screen, so the page can switch its controls:
 *   bit 0 a menu is open, bit 1 a yes/no question is waiting, bit 2 the automap is on,
 *   bit 3 playing a level, bit 4 intermission/finale/title. */
EMSCRIPTEN_KEEPALIVE int am_state(void)
{
  int s = 0;
  if (menuactive) s |= 1;
  if (messageToPrint && messageNeedsInput) s |= 2;
  if (automapmode & am_active) s |= 4;
  if (gamestate == GS_LEVEL) s |= 8;
  else s |= 16;
  return s;
}

/* Write prboom-plus.cfg now (normally only on quit; on the web the tab just closes). */
EMSCRIPTEN_KEEPALIVE void am_save_config(void)
{
  M_SaveDefaults();
}

/* Called once per pass of the main loop: hand control back to the browser until the next
 * animation frame. Paces rendering to the display and keeps the page responsive. */
EM_ASYNC_JS(void, am_wait_frame, (void), {
  await new Promise(function (resolve) {
    if (document.hidden) setTimeout(resolve, 100); else requestAnimationFrame(function () { resolve(); });
  });
});

#endif
