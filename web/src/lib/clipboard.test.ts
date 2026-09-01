import { afterEach, describe, expect, it, vi } from 'vitest'

import { copyTextToClipboard } from './clipboard'

interface TextareaStub {
  value: string
  style: Record<string, string>
  select: ReturnType<typeof vi.fn>
  remove: ReturnType<typeof vi.fn>
}

function stubDom({ execCommandResult }: { execCommandResult: boolean }) {
  const textarea: TextareaStub = {
    value: '',
    style: {},
    select: vi.fn(),
    remove: vi.fn(),
  }
  const execCommand = vi.fn(() => execCommandResult)
  vi.stubGlobal('document', {
    createElement: vi.fn(() => textarea),
    body: { appendChild: vi.fn() },
    execCommand,
  })
  return { textarea, execCommand }
}

function stubClipboard(writeText: ReturnType<typeof vi.fn>) {
  vi.stubGlobal('navigator', { clipboard: { writeText } })
}

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('copyTextToClipboard', () => {
  it('copies via the Clipboard API when available', async () => {
    const writeText = vi.fn().mockResolvedValue(undefined)
    stubClipboard(writeText)

    await expect(copyTextToClipboard('hello')).resolves.toBe(true)
    expect(writeText).toHaveBeenCalledWith('hello')
  })

  it('falls back to execCommand when the Clipboard API rejects', async () => {
    stubClipboard(vi.fn().mockRejectedValue(new Error('denied')))
    const { textarea, execCommand } = stubDom({ execCommandResult: true })

    await expect(copyTextToClipboard('fallback')).resolves.toBe(true)
    expect(textarea.value).toBe('fallback')
    expect(textarea.select).toHaveBeenCalled()
    expect(execCommand).toHaveBeenCalledWith('copy')
    expect(textarea.remove).toHaveBeenCalled()
  })

  it('returns false when both mechanisms fail', async () => {
    stubClipboard(vi.fn().mockRejectedValue(new Error('denied')))
    stubDom({ execCommandResult: false })

    await expect(copyTextToClipboard('nope')).resolves.toBe(false)
  })

  it('returns false when the fallback throws', async () => {
    stubClipboard(vi.fn().mockRejectedValue(new Error('denied')))
    vi.stubGlobal('document', {
      createElement: vi.fn(() => {
        throw new Error('no dom')
      }),
      body: { appendChild: vi.fn() },
      execCommand: vi.fn(),
    })

    await expect(copyTextToClipboard('nope')).resolves.toBe(false)
  })
})
