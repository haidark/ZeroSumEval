for i in {1..20}; do
    find /Users/haidark/ktet_src/output/results_mix_all_mathquiz_no_optim/matches -type d -empty -delete && python run_pool_matches.py -c experiments/mathquiz/mathquiz_pool_mix_no_optim.yaml
done

