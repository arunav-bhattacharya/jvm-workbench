package workbench.memory.l03;

import java.util.Map;
import java.util.WeakHashMap;

/** WeakHashMap drops an entry when its key is unreachable, unless the value refers to the key. */
public class WeakHashMapDemo {
    record Session(String id) {}
    record CheckoutState(String cart) {}
    record SessionAudit(Session session, String note) {}          // refers back to its own key

    public static void main(String[] args) throws InterruptedException {
        Map<Session, CheckoutState> checkouts = new WeakHashMap<>();
        Map<Session, SessionAudit> audits = new WeakHashMap<>();
        Session s1 = new Session("s-1");
        Session s2 = new Session("s-2");
        checkouts.put(s1, new CheckoutState("2 items"));
        audits.put(s2, new SessionAudit(s2, "opened"));

        s1 = null;                                                 // the sessions end: nothing else refers to them
        s2 = null;
        for (int i = 0; i < 5; i++) { System.gc(); Thread.sleep(20); }   // demo only: ask for a few GCs

        System.out.println("checkouts left: " + checkouts.size());       // size() also removes cleared entries
        System.out.println("audits left:    " + audits.size());
    }
}
