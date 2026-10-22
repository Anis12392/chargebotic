/**
 * Offline capture queue.
 *
 * Field crews work where there is no signal. A capture is written to IndexedDB
 * *before* the network is attempted, so losing the connection — or the tab —
 * never loses the photograph or its GPS fix. The queue drains when the browser
 * reports it is back online.
 */

import type { CaptureContext } from './types';

const DB_NAME = 'gridline';
const DB_VERSION = 1;
const STORE = 'pending-captures';

export interface PendingCapture {
  id: string;
  createdAt: number;
  capture: CaptureContext;
  photo: Blob;
  attempts: number;
  lastError?: string;
}

function openDatabase(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    if (typeof indexedDB === 'undefined') {
      reject(new Error('IndexedDB unavailable'));
      return;
    }
    const request = indexedDB.open(DB_NAME, DB_VERSION);
    request.onupgradeneeded = () => {
      const db = request.result;
      if (!db.objectStoreNames.contains(STORE)) {
        const store = db.createObjectStore(STORE, { keyPath: 'id' });
        store.createIndex('createdAt', 'createdAt');
      }
    };
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error ?? new Error('Failed to open IndexedDB'));
  });
}

async function withStore<T>(
  mode: IDBTransactionMode,
  work: (store: IDBObjectStore) => IDBRequest<T>,
): Promise<T> {
  const db = await openDatabase();
  return new Promise<T>((resolve, reject) => {
    const transaction = db.transaction(STORE, mode);
    const request = work(transaction.objectStore(STORE));
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error ?? new Error('IndexedDB operation failed'));
    transaction.oncomplete = () => db.close();
  });
}

export function newCaptureId(): string {
  if (typeof crypto !== 'undefined' && 'randomUUID' in crypto) return crypto.randomUUID();
  return `capture-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;
}

export async function enqueueCapture(capture: CaptureContext, photo: Blob): Promise<PendingCapture> {
  const entry: PendingCapture = {
    id: newCaptureId(),
    createdAt: Date.now(),
    capture,
    photo,
    attempts: 0,
  };
  await withStore('readwrite', (store) => store.put(entry));
  return entry;
}

export async function listPending(): Promise<PendingCapture[]> {
  try {
    const all = await withStore<PendingCapture[]>('readonly', (store) => store.getAll());
    return all.sort((a, b) => a.createdAt - b.createdAt);
  } catch {
    return [];
  }
}

export async function removePending(id: string): Promise<void> {
  try {
    await withStore('readwrite', (store) => store.delete(id));
  } catch {
    // A queue we cannot write to is not worth failing the upload over.
  }
}

export async function recordFailure(id: string, error: string): Promise<void> {
  try {
    const existing = await withStore<PendingCapture | undefined>('readonly', (store) =>
      store.get(id),
    );
    if (!existing) return;
    await withStore('readwrite', (store) =>
      store.put({ ...existing, attempts: existing.attempts + 1, lastError: error }),
    );
  } catch {
    // Best effort.
  }
}

export async function pendingCount(): Promise<number> {
  try {
    return await withStore<number>('readonly', (store) => store.count());
  } catch {
    return 0;
  }
}
