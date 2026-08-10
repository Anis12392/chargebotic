import { redirect } from 'next/navigation';

/** The map is the app now; this keeps older links and the PWA shortcut alive. */
export default function MapRedirect() {
  redirect('/');
}
