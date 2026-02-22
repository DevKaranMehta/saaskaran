import { NextRequest, NextResponse } from 'next/server'

const MAIN_DOMAIN  = 'factory.supportbox.cloud'
const COOKIE_NAME  = 'sf_token'

// Paths that don't require auth (matched on subdomains)
const PUBLIC_PATHS = ['/login', '/register', '/api/']

export function middleware(request: NextRequest) {
  const hostname = request.headers.get('host') || ''
  const { pathname } = request.nextUrl

  // ── Detect subdomain ─────────────────────────────────────────────
  const isSubdomain = hostname.endsWith(`.${MAIN_DOMAIN}`) && hostname !== MAIN_DOMAIN
  if (!isSubdomain) {
    // Main domain — pass through unchanged
    return NextResponse.next()
  }

  const slug = hostname.replace(`.${MAIN_DOMAIN}`, '')

  // ── Public paths on subdomain — allow through ────────────────────
  const isPublic = PUBLIC_PATHS.some(p => pathname.startsWith(p))

  // ── Check auth cookie ────────────────────────────────────────────
  const token = request.cookies.get(COOKIE_NAME)?.value

  if (!token && !isPublic) {
    // Not authenticated — send to subdomain login
    const loginUrl = new URL('/login', request.url)
    loginUrl.searchParams.set('workspace', slug)
    return NextResponse.redirect(loginUrl)
  }

  // ── Pass through — inject tenant slug header for server components ─
  const response = NextResponse.next()
  response.headers.set('x-tenant-slug', slug)
  response.headers.set('x-is-subdomain', '1')
  return response
}

export const config = {
  // Run on all paths except Next.js internals and static files
  matcher: ['/((?!_next/static|_next/image|favicon.ico).*)'],
}
