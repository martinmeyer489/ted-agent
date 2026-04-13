import { NextRequest, NextResponse } from 'next/server'

export const runtime = 'edge'

const BACKEND_URL = process.env.BACKEND_URL || 'http://91.99.141.177:8000'
const API_KEY = process.env.BACKEND_API_KEY || ''

export async function GET(request: NextRequest) {
  const path = request.nextUrl.pathname.replace('/api/proxy', '')
  const searchParams = request.nextUrl.searchParams.toString()
  const url = `${BACKEND_URL}${path}${searchParams ? `?${searchParams}` : ''}`

  try {
    const headers: HeadersInit = {}
    if (API_KEY) headers['x-api-key'] = API_KEY
    const auth = request.headers.get('authorization')
    if (auth) headers['Authorization'] = auth

    const response = await fetch(url, { method: 'GET', headers })
    const data = await response.json()
    return NextResponse.json(data, { status: response.status })
  } catch (error) {
    console.error('Proxy GET error:', error)
    return NextResponse.json(
      { error: 'Failed to fetch from backend' },
      { status: 500 }
    )
  }
}

export async function POST(request: NextRequest) {
  const path = request.nextUrl.pathname.replace('/api/proxy', '')
  const url = `${BACKEND_URL}${path}`

  try {
    const contentType = request.headers.get('content-type') || ''

    // Forward auth + API key headers
    const headers: Record<string, string> = {}
    if (API_KEY) headers['x-api-key'] = API_KEY
    const auth = request.headers.get('authorization')
    if (auth) headers['Authorization'] = auth

    let body: BodyInit
    if (contentType.includes('multipart/form-data')) {
      // FormData: pass through as-is (used by /agents/{id}/runs)
      body = await request.arrayBuffer()
      headers['content-type'] = contentType // keep boundary intact
    } else {
      // JSON or other
      body = await request.text()
      headers['content-type'] = 'application/json'
    }

    const response = await fetch(url, { method: 'POST', headers, body })

    // Stream SSE responses back (used by /agents/{id}/runs with stream=true)
    const resContentType = response.headers.get('content-type') || ''
    if (resContentType.includes('text/event-stream')) {
      return new NextResponse(response.body, {
        status: response.status,
        headers: {
          'Content-Type': 'text/event-stream',
          'Cache-Control': 'no-cache',
          'Connection': 'keep-alive',
        },
      })
    }

    const data = await response.json()
    return NextResponse.json(data, { status: response.status })
  } catch (error) {
    console.error('Proxy POST error:', error)
    return NextResponse.json(
      { error: 'Failed to fetch from backend' },
      { status: 500 }
    )
  }
}

export async function DELETE(request: NextRequest) {
  const path = request.nextUrl.pathname.replace('/api/proxy', '')
  const url = `${BACKEND_URL}${path}`

  try {
    const headers: HeadersInit = {}
    if (API_KEY) headers['x-api-key'] = API_KEY
    const auth = request.headers.get('authorization')
    if (auth) headers['Authorization'] = auth

    const response = await fetch(url, { method: 'DELETE', headers })
    const data = await response.json()
    return NextResponse.json(data, { status: response.status })
  } catch (error) {
    console.error('Proxy DELETE error:', error)
    return NextResponse.json(
      { error: 'Failed to fetch from backend' },
      { status: 500 }
    )
  }
}
