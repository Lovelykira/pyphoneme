from app.phoneme_parser import TextSynthesis

if __name__ == '__main__':
    text = 'This tests whether 2 samples are drawn from the same distribution. Note that, like in the case of the one-sample K-S test, the distribution is assumed to be continuous.' + \
    'This is the two-sided test, one-sided tests are not implemented. The test uses the two-sided asymptotic Kolmogorov-Smirnov distribution.' + \
    'If the K-S statistic is small or the p-value is high, then we cannot reject the hypothesis that the distributions of the two samples are the same.'
    TextSynthesis(text=text).synthesize_by_deleting_chunks()
