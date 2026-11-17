package workbench.patterns.l09;

import java.util.HashSet;
import java.util.List;
import java.util.Set;

/** A complaint passes along the shop's desk: each handler answers it or passes it on. The order of the list is behavior. */
public class ComplaintDeskDemo {
    record Complaint(String orderNo, String about, int worthCents, boolean hasReceipt) {}
    record Reply(String from, String says) {}

    interface Chain { Reply passOn(Complaint c); }
    interface Handler { Reply handle(Complaint c, Chain next); }

    // fold the handlers into one chain, from the last to the first
    static Chain chain(List<Handler> handlers, Chain lastStop) {
        Chain next = lastStop;
        for (int i = handlers.size() - 1; i >= 0; i--) {
            Handler h = handlers.get(i);
            Chain rest = next;
            next = c -> h.handle(c, rest);
        }
        return next;
    }

    static int sorted = 0;

    static Reply sort(String who) {
        sorted++;
        return new Reply(who, "sorted");
    }

    public static void main(String[] args) {
        Set<String> handled = new HashSet<>();

        Handler book = (c, next) -> {
            Reply r = next.passOn(c);                                    // in: nothing; out: write it in the book
            System.out.println("  book: " + c.orderNo() + " " + c.about() + " -> " + r.from());
            return r;
        };
        Handler receipt = (c, next) -> c.hasReceipt()
                ? next.passOn(c)
                : new Reply("assistant", "please bring the receipt");     // answer now: the rest never runs
        Handler oncePerOrder = (c, next) -> handled.add(c.orderNo())
                ? next.passOn(c)
                : new Reply("assistant", "we sorted this one already");
        Handler assistant = (c, next) -> c.worthCents() <= 500 ? sort("assistant") : next.passOn(c);
        Handler manager = (c, next) -> c.worthCents() <= 5_000 ? sort("manager") : next.passOn(c);
        Chain headOffice = c -> sort("head office");                     // the last stop answers everything

        Chain desk = chain(List.of(book, receipt, oncePerOrder, assistant, manager), headOffice);

        for (Complaint c : List.of(
                new Complaint("7781", "cracked teapot", 1_800, true),
                new Complaint("7781", "cracked teapot", 1_800, true),     // the same complaint again
                new Complaint("7782", "stale bread", 250, false),         // receipt left at home
                new Complaint("7782", "stale bread", 250, true))) {       // back with the receipt
            Reply r = desk.passOn(c);
            System.out.println(r.from() + ": " + r.says());
        }
        System.out.println("complaints sorted: " + sorted);
    }
}
