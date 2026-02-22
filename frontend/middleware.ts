import { NextRequest, NextResponse } from 'next/server'

const MAIN_DOMAIN  = 'factory.supportbox.cloud'
const COOKIE_NAME  = 'sf_token'

// Paths that never require auth
const PUBLIC_PATHS = ['/login', '/register', '/api/', '/workspace-preview']

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
    if (pathname === '/') {
      // Root of workspace subdomain — show public workspace preview
      const previewUrl = new URL('/workspace-preview', request.url)
      previewUrl.searchParams.set('workspace', slug)
      return NextResponse.redirect(previewUrl)
    }
    // Other protected paths — redirect to workspace login
    const loginUrl = new URL('/login', request.url)
    loginUrl.searchParams.set('workspace', slug)
    return NextResponse.redirect(loginUrl)
  }

  // ── Pass through — inject tenant slug header ──────────────────────
  const response = NextResponse.next()
  response.headers.set('x-tenant-slug', slug)
  response.headers.set('x-is-subdomain', '1')
  return response
}

export const config = {
  // Run on all paths except Next.js internals and static files
  matcher: ['/((?!_next/static|_next/image|favicon.ico).*)'],
}
