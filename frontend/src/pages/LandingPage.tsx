import React, { useEffect, useState } from 'react';
import { FiMessageSquare, FiZap, FiShield, FiGlobe, FiArrowRight, FiCheck } from 'react-icons/fi';
import SpaceBackground from '../components/SpaceBackground';

interface LandingPageProps {
  onLoginClick: () => void;
}

const LandingPage: React.FC<LandingPageProps> = ({ onLoginClick }) => {
  const [isVisible, setIsVisible] = useState(false);
  const [scrollY, setScrollY] = useState(0);

  useEffect(() => {
    setIsVisible(true);
    
    const handleScroll = () => {
      setScrollY(window.scrollY);
    };
    
    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  return (
    <div className="min-h-screen bg-black overflow-x-hidden">
      {/* 3D Space Background */}
      <SpaceBackground />
      
      {/* Navigation */}
      <nav className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
        scrollY > 50 ? 'space-glass border-b border-white/10' : 'bg-transparent'
      }`}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-14 sm:h-16">
            <div className="flex items-center gap-2 sm:gap-3">
              <div className="w-8 h-8 sm:w-10 sm:h-10 rounded-xl bg-gradient-to-br from-apple-accent to-blue-600 flex items-center justify-center">
                <FiMessageSquare className="w-4 h-4 sm:w-5 sm:h-5 text-white" />
              </div>
              <span className="text-lg sm:text-xl font-semibold text-apple-text">Alice AI</span>
            </div>
            <button
              onClick={onLoginClick}
              className="px-4 sm:px-6 py-2 sm:py-2.5 rounded-full bg-gradient-to-r from-[#0A84FF] via-[#5E5CE6] to-[#BF5AF2] hover:shadow-[0_0_20px_rgba(94,92,230,0.5)] text-white text-sm sm:text-base font-medium transition-all duration-300 hover:scale-105 active:scale-95"
            >
              Login
            </button>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative min-h-screen flex items-center justify-center pt-16 overflow-hidden">
        {/* Background is now handled by SpaceBackground component */}
        
        <div className={`relative z-10 max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 text-center transition-all duration-1000 ${
          isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-10'
        }`}>
          {/* Badge */}
          <div className="inline-flex items-center gap-2 px-3 sm:px-4 py-1.5 sm:py-2 rounded-full bg-apple-surface/80 border border-apple-border mb-6 sm:mb-8">
            <span className="w-2 h-2 rounded-full bg-apple-green animate-pulse" />
            <span className="text-xs sm:text-sm text-apple-secondary">Powered by Advanced AI</span>
          </div>
          
          {/* Main headline */}
          <h1 className="text-4xl sm:text-5xl md:text-6xl lg:text-7xl font-bold text-apple-text leading-tight tracking-tight mb-4 sm:mb-6">
            Meet <span className="bg-gradient-to-r from-apple-accent via-blue-400 to-purple-500 bg-clip-text text-transparent">Alice</span>
            <br />
            <span className="text-3xl sm:text-4xl md:text-5xl lg:text-6xl">Your Intelligent Assistant</span>
          </h1>
          
          {/* Subtitle */}
          <p className="text-base sm:text-lg md:text-xl text-apple-secondary max-w-2xl mx-auto mb-8 sm:mb-10 leading-relaxed px-4">
            Experience the next generation of conversational AI. Smart, intuitive, and designed to help you accomplish more.
          </p>
          
          {/* CTA Buttons */}
          <div className="flex flex-col sm:flex-row items-center justify-center gap-3 sm:gap-4">
            <button
              onClick={onLoginClick}
              className="w-full sm:w-auto group flex items-center justify-center gap-2 px-6 sm:px-8 py-3 sm:py-4 rounded-full bg-apple-accent hover:bg-apple-accentHover text-white text-base sm:text-lg font-semibold transition-all duration-300 hover:scale-105 active:scale-95 hover:shadow-lg hover:shadow-apple-accent/30"
            >
              Get Started Free
              <FiArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
            </button>
            <a
              href="#features"
              className="w-full sm:w-auto flex items-center justify-center gap-2 px-6 sm:px-8 py-3 sm:py-4 rounded-full border border-apple-border text-apple-text text-base sm:text-lg font-medium hover:bg-apple-surface/50 transition-all duration-200"
            >
              Learn More
            </a>
          </div>
        </div>
        
        {/* Scroll indicator */}
        <div className="absolute bottom-8 left-1/2 -translate-x-1/2 animate-bounce hidden sm:block">
          <div className="w-6 h-10 rounded-full border-2 border-apple-border flex items-start justify-center pt-2">
            <div className="w-1 h-3 bg-apple-secondary rounded-full animate-pulse" />
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="py-16 sm:py-24 lg:py-32 bg-apple-surface">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12 sm:mb-16">
            <h2 className="text-2xl sm:text-3xl md:text-4xl lg:text-5xl font-bold text-apple-text mb-4 sm:mb-6">
              Why Choose Alice?
            </h2>
            <p className="text-base sm:text-lg text-apple-secondary max-w-2xl mx-auto">
              Designed with simplicity and power in mind. Alice brings cutting-edge AI to your fingertips.
            </p>
          </div>
          
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6 lg:gap-8">
            <FeatureCard
              icon={<FiZap className="w-6 h-6 sm:w-7 sm:h-7" />}
              title="Lightning Fast"
              description="Get instant responses powered by advanced language models. No waiting, just results."
              delay={0}
            />
            <FeatureCard
              icon={<FiShield className="w-6 h-6 sm:w-7 sm:h-7" />}
              title="Secure & Private"
              description="Your conversations are encrypted and protected. Your privacy is our priority."
              delay={100}
            />
            <FeatureCard
              icon={<FiMessageSquare className="w-6 h-6 sm:w-7 sm:h-7" />}
              title="Natural Conversations"
              description="Chat naturally like you would with a friend. Alice understands context and nuance."
              delay={200}
            />
            <FeatureCard
              icon={<FiGlobe className="w-6 h-6 sm:w-7 sm:h-7" />}
              title="Always Available"
              description="Access Alice anytime, anywhere. Available 24/7 across all your devices."
              delay={300}
            />
          </div>
        </div>
      </section>

      {/* Showcase Section */}
      <section className="py-16 sm:py-24 lg:py-32 bg-apple-bg">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 sm:gap-12 lg:gap-16 items-center">
            <div className="order-2 lg:order-1">
              <h2 className="text-2xl sm:text-3xl md:text-4xl font-bold text-apple-text mb-4 sm:mb-6">
                Powerful yet Simple
              </h2>
              <p className="text-base sm:text-lg text-apple-secondary mb-6 sm:mb-8 leading-relaxed">
                Alice combines the most advanced AI technology with an intuitive interface that anyone can use. 
                No learning curve, just pure productivity.
              </p>
              <ul className="space-y-3 sm:space-y-4">
                <CheckItem text="Upload files and images for analysis" />
                <CheckItem text="Maintain context across conversations" />
                <CheckItem text="Get help with coding, writing, and more" />
                <CheckItem text="Export and share your conversations" />
              </ul>
            </div>
            <div className="order-1 lg:order-2">
              {/* Chat mockup */}
              <div className="relative">
                <div className="absolute inset-0 bg-gradient-to-r from-apple-accent/20 to-purple-500/20 rounded-2xl sm:rounded-3xl blur-2xl" />
                <div className="relative bg-apple-surface rounded-2xl sm:rounded-3xl p-4 sm:p-6 border border-apple-border shadow-2xl">
                  <div className="flex items-center gap-2 mb-4 sm:mb-6 pb-4 border-b border-apple-border">
                    <div className="flex gap-1.5 sm:gap-2">
                      <div className="w-2.5 h-2.5 sm:w-3 sm:h-3 rounded-full bg-apple-red" />
                      <div className="w-2.5 h-2.5 sm:w-3 sm:h-3 rounded-full bg-apple-orange" />
                      <div className="w-2.5 h-2.5 sm:w-3 sm:h-3 rounded-full bg-apple-green" />
                    </div>
                    <span className="ml-2 sm:ml-4 text-xs sm:text-sm text-apple-secondary">Alice Chat</span>
                  </div>
                  <div className="space-y-3 sm:space-y-4">
                    <div className="flex justify-end">
                      <div className="bg-apple-accent rounded-2xl rounded-br-md px-3 sm:px-4 py-2 sm:py-2.5 max-w-[85%] sm:max-w-[80%]">
                        <p className="text-white text-sm sm:text-base">Can you help me write a compelling product description?</p>
                      </div>
                    </div>
                    <div className="flex justify-start">
                      <div className="bg-apple-elevated rounded-2xl rounded-bl-md px-3 sm:px-4 py-2 sm:py-2.5 max-w-[85%] sm:max-w-[80%]">
                        <p className="text-apple-text text-sm sm:text-base">Of course! I'd be happy to help. What product would you like me to describe, and who is your target audience?</p>
                      </div>
                    </div>
                    <div className="flex justify-end">
                      <div className="bg-apple-accent rounded-2xl rounded-br-md px-3 sm:px-4 py-2 sm:py-2.5 max-w-[85%] sm:max-w-[80%]">
                        <p className="text-white text-sm sm:text-base">It's a smart home device for tech-savvy millennials</p>
                      </div>
                    </div>
                    <div className="flex justify-start items-end gap-1.5 sm:gap-2">
                      <div className="bg-apple-elevated rounded-2xl rounded-bl-md px-3 sm:px-4 py-2 sm:py-2.5">
                        <div className="flex gap-1">
                          <div className="w-2 h-2 rounded-full bg-apple-secondary typing-dot" />
                          <div className="w-2 h-2 rounded-full bg-apple-secondary typing-dot" />
                          <div className="w-2 h-2 rounded-full bg-apple-secondary typing-dot" />
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-16 sm:py-24 lg:py-32 relative z-10">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-2xl sm:text-3xl md:text-4xl lg:text-5xl font-bold text-white mb-4 sm:mb-6">
            Ready to Get Started?
          </h2>
          <p className="text-base sm:text-lg text-apple-secondary mb-8 sm:mb-10 max-w-2xl mx-auto">
            Join thousands of users who are already experiencing the future of AI assistance. 
            It only takes a few seconds to begin.
          </p>
          <button
            onClick={onLoginClick}
            className="group inline-flex items-center gap-2 px-8 sm:px-10 py-3 sm:py-4 rounded-full bg-gradient-to-r from-[#0A84FF] via-[#5E5CE6] to-[#BF5AF2] text-white text-base sm:text-lg font-semibold transition-all duration-300 hover:scale-105 active:scale-95 hover:shadow-[0_0_30px_rgba(94,92,230,0.5)]"
          >
            Start Chatting Now
            <FiArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
          </button>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-8 sm:py-12 relative z-10 border-t border-white/10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-2 sm:gap-3">
              <div className="w-7 h-7 sm:w-8 sm:h-8 rounded-lg bg-gradient-to-br from-[#0A84FF] via-[#5E5CE6] to-[#BF5AF2] flex items-center justify-center">
                <FiMessageSquare className="w-3.5 h-3.5 sm:w-4 sm:h-4 text-white" />
              </div>
              <span className="text-base sm:text-lg font-semibold text-white">Alice AI</span>
            </div>
            <p className="text-xs sm:text-sm text-apple-secondary">
              © 2024 Alice AI. All rights reserved.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
};

interface FeatureCardProps {
  icon: React.ReactNode;
  title: string;
  description: string;
  delay: number;
}

const FeatureCard: React.FC<FeatureCardProps> = ({ icon, title, description, delay }) => {
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => setIsVisible(true), delay);
    return () => clearTimeout(timer);
  }, [delay]);

  return (
    <div
      className={`group p-5 sm:p-6 lg:p-8 rounded-2xl sm:rounded-3xl space-glass border border-white/10 hover:border-purple-500/50 transition-all duration-500 hover:scale-[1.02] hover:shadow-[0_0_30px_rgba(94,92,230,0.2)] ${
        isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'
      }`}
    >
      <div className="w-12 h-12 sm:w-14 sm:h-14 rounded-xl sm:rounded-2xl bg-gradient-to-br from-[#0A84FF] via-[#5E5CE6] to-[#BF5AF2] flex items-center justify-center mb-4 sm:mb-6 text-white group-hover:scale-110 transition-transform duration-300 shadow-lg shadow-purple-500/30">
        {icon}
      </div>
      <h3 className="text-lg sm:text-xl font-semibold text-white mb-2 sm:mb-3">{title}</h3>
      <p className="text-sm sm:text-base text-apple-secondary leading-relaxed">{description}</p>
    </div>
  );
};

interface CheckItemProps {
  text: string;
}

const CheckItem: React.FC<CheckItemProps> = ({ text }) => (
  <li className="flex items-center gap-3">
    <div className="w-5 h-5 sm:w-6 sm:h-6 rounded-full bg-apple-green/20 flex items-center justify-center flex-shrink-0">
      <FiCheck className="w-3 h-3 sm:w-3.5 sm:h-3.5 text-apple-green" />
    </div>
    <span className="text-sm sm:text-base text-apple-text">{text}</span>
  </li>
);

export default LandingPage;
