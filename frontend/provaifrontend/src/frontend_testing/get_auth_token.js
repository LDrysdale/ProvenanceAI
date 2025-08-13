import { getAuth } from "firebase/auth";

const auth = getAuth();

auth.currentUser.getIdToken(/* forceRefresh */ true).then((idToken) => {
  console.log("Firebase ID Token:", idToken);
  // Use this token in your test script's Authorization header as: `Bearer ${idToken}`
});
