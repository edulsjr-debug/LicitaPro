import { cookies } from 'next/headers'
import { NextResponse } from 'next/server'

export async function POST(request: Request) {
  const { password } = await request.json()
  const expected = process.env.AUTH_PASSWORD ?? 'licitapro'

  if (password !== expected) {
    return NextResponse.json({ error: 'Senha incorreta' }, { status: 401 })
  }

  const cookieStore = await cookies()
  cookieStore.set('licitapro_auth', btoa(expected), {
    httpOnly: true,
    secure: process.env.NODE_ENV === 'production',
    sameSite: 'lax',
    maxAge: 60 * 60 * 24 * 30,
    path: '/',
  })

  return NextResponse.json({ ok: true })
}
