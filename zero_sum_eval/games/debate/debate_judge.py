import dspy
from dataclasses import dataclass

class ArgumentationSignature(dspy.Signature):
    """You are a debate judge evaluating the quality of argumentation presented by a specific side. 
    Your role is to assess the clarity, logical consistency, and relevance of the arguments made."""
    
    topic = dspy.InputField(desc="The debate resolution or central issue under discussion.")
    history = dspy.InputField(desc="The full history of the debate, including arguments, counterarguments, and rebuttals made so far.")
    side: str = dspy.InputField(desc="The side you are evaluating ('for' or 'against').")
    
    clarity: int = dspy.OutputField(desc="How clearly and effectively are the arguments presented? (1 = very unclear, 5 = exceptionally clear and precise).")
    coherence: int = dspy.OutputField(desc="How logically structured and internally consistent are the arguments? (1 = highly disorganized, 5 = flawlessly logical and well-reasoned).")
    relevance: int = dspy.OutputField(desc="How directly do the arguments address the debate topic? (1 = largely off-topic, 5 = fully relevant and well-connected).")


class EvidenceSignature(dspy.Signature):
    """You are a debate judge evaluating the use of evidence by a particular side. 
    Your role is to assess how well they incorporate and analyze supporting evidence."""
    
    topic = dspy.InputField(desc="The debate resolution or central issue under discussion.")
    history = dspy.InputField(desc="The full history of the debate, including arguments, counterarguments, and rebuttals made so far.")
    side: str = dspy.InputField(desc="The side you are evaluating ('for' or 'against').")
    
    use_of_evidence: int = dspy.OutputField(desc="How effectively does this side integrate evidence to support their claims? (1 = minimal or no evidence, 5 = extensive and well-integrated evidence).")
    credibility: int = dspy.OutputField(desc="How reliable and authoritative are the sources they cite? (1 = questionable or weak sources, 5 = highly credible, authoritative sources).")
    depth_of_analysis: int = dspy.OutputField(desc="To what extent does this side critically analyze and interpret the evidence? (1 = superficial use, 5 = deeply analyzed and well-contextualized evidence).")


class RebuttalSignature(dspy.Signature):
    """You are a debate judge evaluating the strength and effectiveness of a side’s rebuttals. 
    Your role is to assess how well they respond to their opponent’s arguments."""
    
    topic = dspy.InputField(desc="The debate resolution or central issue under discussion.")
    history = dspy.InputField(desc="The full history of the debate, including arguments, counterarguments, and rebuttals made so far.")
    side: str = dspy.InputField(desc="The side you are evaluating ('for' or 'against').")
    
    responsiveness: int = dspy.OutputField(desc="How directly and effectively does this side respond to the opponent’s arguments? (1 = largely ignores key points, 5 = thoroughly addresses and refutes opponent’s claims).")
    effectiveness: int = dspy.OutputField(desc="How persuasive and impactful are their rebuttals? (1 = weak and unconvincing, 5 = highly persuasive and well-reasoned).")
    balance: int = dspy.OutputField(desc="How well does this side balance refuting their opponent’s claims while reinforcing their own stance? (1 = overly aggressive or defensive, 5 = strategic and well-balanced).")


class PresentationSignature(dspy.Signature):
    """You are a debate judge evaluating the presentation and delivery of arguments by a specific side. 
    Your role is to assess clarity, engagement, and structural organization."""
    
    topic = dspy.InputField(desc="The debate resolution or central issue under discussion.")
    history = dspy.InputField(desc="The full history of the debate, including arguments, counterarguments, and rebuttals made so far.")
    side: str = dspy.InputField(desc="The side you are evaluating ('for' or 'against').")
    
    conciseness: int = dspy.OutputField(desc="How well does this side articulate their points without unnecessary repetition or verbosity? (1 = rambling and unfocused, 5 = clear and to the point).")
    engagement: int = dspy.OutputField(desc="How persuasive and engaging is their argument delivery? (1 = dull and unconvincing, 5 = highly compelling and rhetorically strong).")
    organization: int = dspy.OutputField(desc="How logically structured and easy to follow is their presentation? (1 = chaotic and difficult to follow, 5 = well-structured and seamless).")


class OverallPerformanceSignature(dspy.Signature):
    """You are a debate judge providing an overall assessment of a side’s performance in the debate. 
    Your role is to evaluate their persuasiveness, originality, and fairness in argumentation."""
    
    topic = dspy.InputField(desc="The debate resolution or central issue under discussion.")
    history = dspy.InputField(desc="The full history of the debate, including arguments, counterarguments, and rebuttals made so far.")
    side: str = dspy.InputField(desc="The side you are evaluating ('for' or 'against').")
    
    persuasiveness: int = dspy.OutputField(desc="How effectively does this side convince the judge/audience of their position? (1 = unpersuasive, 5 = highly compelling and well-argued).")
    originality: int = dspy.OutputField(desc="How unique and creative are their arguments? (1 = generic and repetitive, 5 = highly innovative and insightful).")
    fairness: int = dspy.OutputField(desc="To what extent does this side adhere to ethical debating principles, avoiding misrepresentation or logical fallacies? (1 = unfair and misleading, 5 = intellectually honest and fair-minded).")


@dataclass
class RubricWeights:
    argumentation: int = 30
    rebuttal: int = 30
    evidence: int = 15
    overall_performance: int = 15
    presentation: int = 10


class DebateJudge(dspy.Module):
    def __init__(self, weights=None):
        self.argumentation = dspy.ChainOfThought(ArgumentationSignature)
        self.evidence = dspy.ChainOfThought(EvidenceSignature)
        self.rebuttal = dspy.ChainOfThought(RebuttalSignature)
        self.presentation = dspy.ChainOfThought(PresentationSignature)
        self.overall_performance = dspy.ChainOfThought(OverallPerformanceSignature)
        self.weights = weights if weights else RubricWeights()

    def forward(self, topic, history, side, rubric_weights=None):
        # Evaluate each rubric category for the given side
        arg_scores = self.argumentation(topic=topic, history=history, side=side)
        ev_scores = self.evidence(topic=topic, history=history, side=side)
        rebuttal_scores = self.rebuttal(topic=topic, history=history, side=side)
        presentation_scores = self.presentation(topic=topic, history=history, side=side)
        overall_scores = self.overall_performance(
            topic=topic, history=history, side=side
        )

        # Aggregate scores (weighted)
        total_score = (
            (arg_scores.clarity + arg_scores.coherence + arg_scores.relevance)
            * self.weights.argumentation
            + (
                ev_scores.use_of_evidence
                + ev_scores.credibility
                + ev_scores.depth_of_analysis
            )
            * self.weights.evidence
            + (
                rebuttal_scores.responsiveness
                + rebuttal_scores.effectiveness
                + rebuttal_scores.balance
            )
            * self.weights.rebuttal
            + (
                presentation_scores.conciseness
                + presentation_scores.engagement
                + presentation_scores.organization
            )
            * self.weights.presentation
            + (
                overall_scores.persuasiveness
                + overall_scores.originality
                + overall_scores.fairness
            )
            * self.weights.overall_performance
        ) / 100

        return dspy.Prediction(
            argumentation=arg_scores.toDict(),
            evidence=ev_scores.toDict(),
            rebuttal=rebuttal_scores.toDict(),
            presentation=presentation_scores.toDict(),
            overall_performance=overall_scores.toDict(),
            weighted_score=total_score,
        )
