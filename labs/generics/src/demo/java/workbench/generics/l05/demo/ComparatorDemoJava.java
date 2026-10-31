package workbench.generics.l05.demo;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;

/** Java twin of ComparatorDemo.kt. List.sort takes a Comparator<? super E>. */
public class ComparatorDemoJava {

    static final Comparator<PaymentEvent> BY_PAYMENT_ID = Comparator.comparing(PaymentEvent::getPaymentId);

    public static void main(String[] args) {
        List<CardAuthorized> auths = new ArrayList<>(List.of(new CardAuthorized("pay_3", 1_200), new CardAuthorized("pay_1", 350)));
        List<RefundIssued> refunds = new ArrayList<>(List.of(new RefundIssued("pay_9", 50), new RefundIssued("pay_4", 75)));

        List<CardAuthorized> sortedAuths = new ArrayList<>(auths);
        sortedAuths.sort(BY_PAYMENT_ID);    // List<E>.sort(Comparator<? super E>)
        List<RefundIssued> sortedRefunds = new ArrayList<>(refunds);
        sortedRefunds.sort(BY_PAYMENT_ID);
        System.out.println(sortedAuths.stream().map(PaymentEvent::getPaymentId).toList());
        System.out.println(sortedRefunds.stream().map(PaymentEvent::getPaymentId).toList());

        Comparator<? super CardAuthorized> forCards = BY_PAYMENT_ID;

        // Wrong move. Uncomment, predict the error, then run.
        // Comparator<CardAuthorized> strict = BY_PAYMENT_ID;
        System.out.println("forCards compares: " + forCards.compare(auths.get(0), auths.get(1)));
    }
}
