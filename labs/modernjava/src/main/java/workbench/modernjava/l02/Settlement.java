package workbench.modernjava.l02;

import workbench.modernjava.l02.PaymentMethod.BankTransfer;
import workbench.modernjava.l02.PaymentMethod.Card;
import workbench.modernjava.l02.PaymentMethod.PartnerMethod;
import workbench.modernjava.l02.PaymentMethod.Sepa;
import workbench.modernjava.l02.PaymentMethod.Swift;
import workbench.modernjava.l02.PaymentMethod.Wallet;

/** Settlement rules, one exhaustive switch per rule. No {@code default} anywhere. */
public final class Settlement {
    private Settlement() {}

    /**
     * TODO 4: business days until the money reaches the merchant.
     * Card 2, Sepa 1, Swift 3, Wallet 0, and a PartnerMethod says for itself ({@code settlementDays()}).
     * Write a switch with one case per type and no {@code default}. Once the hierarchy is sealed,
     * javac accepts it; before that, it can't.
     */
    public static int daysToSettle(PaymentMethod method) {
        throw new UnsupportedOperationException("TODO: daysToSettle");
    }

    /**
     * TODO 5: the rail name the ledger records: {@code "card"}, {@code "bank"} for both kinds of
     * transfer, {@code "wallet"}, and {@code "partner:" + partnerId()} for a partner method.
     * Use one case for all bank transfers: {@code BankTransfer} is sealed, so one case covers it.
     */
    public static String rail(PaymentMethod method) {
        throw new UnsupportedOperationException("TODO: rail");
    }
}
