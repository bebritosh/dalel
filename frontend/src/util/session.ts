// Case access token is kept in sessionStorage under "case:{id}".

export function tokenKey(caseId: number | string): string {
  return `case:${caseId}`;
}

export function getToken(caseId: number | string): string | null {
  try {
    return sessionStorage.getItem(tokenKey(caseId));
  } catch {
    return null;
  }
}

export function setToken(caseId: number | string, token: string): void {
  try {
    sessionStorage.setItem(tokenKey(caseId), token);
  } catch {
    /* ignore */
  }
}

export function clearToken(caseId: number | string): void {
  try {
    sessionStorage.removeItem(tokenKey(caseId));
  } catch {
    /* ignore */
  }
}
