import React, { useState, useEffect } from 'react';
import { 
  PlusIcon, 
  PencilIcon, 
  TrashIcon, 
  CheckIcon,
  XMarkIcon,
  ChartBarIcon,
  PlayIcon
} from '@heroicons/react/24/outline';

const AidaProductManager = () => {
  const [products, setProducts] = useState([]);
  const [activeProduct, setActiveProduct] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editingProduct, setEditingProduct] = useState(null);
  const [formData, setFormData] = useState({
    brand_name: '',
    product_name: '',
    category: 'service',
    product_type: 'medium',
    offer_tagline: '',
    features: [],
    benefits: [],
    emotion_tone: 'friendly',
    call_to_action: '',
    attention_hooks: [],
    interest_questions: [],
    desire_statements: [],
    action_prompts: [],
    objection_responses: {
      price: [],
      timing: [],
      authority: [],
      need: [],
      competition: [],
      disinterest: []
    }
  });

  useEffect(() => {
    fetchProducts();
    fetchActiveProduct();
  }, []);

  const fetchProducts = async () => {
    try {
      const response = await fetch('/api/aida', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      const data = await response.json();
      if (data.success) {
        setProducts(data.data);
      }
    } catch (error) {
      console.error('Error fetching products:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchActiveProduct = async () => {
    try {
      const response = await fetch('/api/aida/active', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      const data = await response.json();
      if (data.success) {
        setActiveProduct(data.data);
      }
    } catch (error) {
      console.error('Error fetching active product:', error);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const url = editingProduct ? `/api/aida/${editingProduct._id}` : '/api/aida';
      const method = editingProduct ? 'PUT' : 'POST';
      
      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify(formData)
      });
      
      const data = await response.json();
      if (data.success) {
        await fetchProducts();
        setShowForm(false);
        setEditingProduct(null);
        resetForm();
      }
    } catch (error) {
      console.error('Error saving product:', error);
    }
  };

  const handleEdit = (product) => {
    setEditingProduct(product);
    setFormData({
      ...product,
      features: product.features || [],
      benefits: product.benefits || [],
      attention_hooks: product.attention_hooks || [],
      interest_questions: product.interest_questions || [],
      desire_statements: product.desire_statements || [],
      action_prompts: product.action_prompts || [],
      objection_responses: product.objection_responses || {
        price: [], timing: [], authority: [], need: [], competition: [], disinterest: []
      }
    });
    setShowForm(true);
  };

  const handleDelete = async (productId) => {
    if (window.confirm('Are you sure you want to delete this product?')) {
      try {
        const response = await fetch(`/api/aida/${productId}`, {
          method: 'DELETE',
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          }
        });
        
        const data = await response.json();
        if (data.success) {
          await fetchProducts();
        }
      } catch (error) {
        console.error('Error deleting product:', error);
      }
    }
  };

  const handleSetActive = async (productId) => {
    try {
      const response = await fetch('/api/aida/set-active', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({ productId })
      });
      
      const data = await response.json();
      if (data.success) {
        await fetchActiveProduct();
        await fetchProducts();
      }
    } catch (error) {
      console.error('Error setting active product:', error);
    }
  };

  const resetForm = () => {
    setFormData({
      brand_name: '',
      product_name: '',
      category: 'service',
      product_type: 'medium',
      offer_tagline: '',
      features: [],
      benefits: [],
      emotion_tone: 'friendly',
      call_to_action: '',
      attention_hooks: [],
      interest_questions: [],
      desire_statements: [],
      action_prompts: [],
      objection_responses: {
        price: [], timing: [], authority: [], need: [], competition: [], disinterest: []
      }
    });
  };

  const addArrayItem = (field, value) => {
    if (value.trim()) {
      setFormData(prev => ({
        ...prev,
        [field]: [...prev[field], value.trim()]
      }));
    }
  };

  const removeArrayItem = (field, index) => {
    setFormData(prev => ({
      ...prev,
      [field]: prev[field].filter((_, i) => i !== index)
    }));
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold text-gray-900">AIDA Product Manager</h1>
        <button
          onClick={() => setShowForm(true)}
          className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg flex items-center gap-2"
        >
          <PlusIcon className="h-5 w-5" />
          New Product
        </button>
      </div>

      {/* Active Product Display */}
      {activeProduct && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-6">
          <div className="flex items-center gap-2 mb-2">
            <CheckIcon className="h-5 w-5 text-green-500" />
            <h3 className="text-lg font-semibold text-green-800">Active Product</h3>
          </div>
          <p className="text-green-700">
            <strong>{activeProduct.brand_name}</strong> - {activeProduct.product_name}
          </p>
          <p className="text-sm text-green-600 mt-1">{activeProduct.offer_tagline}</p>
        </div>
      )}

      {/* Products List */}
      <div className="grid gap-4">
        {products.map((product) => (
          <div key={product._id} className="bg-white border border-gray-200 rounded-lg p-4">
            <div className="flex justify-between items-start">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-2">
                  <h3 className="text-lg font-semibold text-gray-900">
                    {product.brand_name} - {product.product_name}
                  </h3>
                  {product.isActive && (
                    <span className="bg-green-100 text-green-800 text-xs px-2 py-1 rounded-full">
                      Active
                    </span>
                  )}
                  <span className={`text-xs px-2 py-1 rounded-full ${
                    product.product_type === 'high' ? 'bg-red-100 text-red-800' :
                    product.product_type === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                    'bg-blue-100 text-blue-800'
                  }`}>
                    {product.product_type} ticket
                  </span>
                </div>
                <p className="text-gray-600 mb-2">{product.offer_tagline}</p>
                <div className="flex gap-2 text-sm text-gray-500">
                  <span>Category: {product.category}</span>
                  <span>•</span>
                  <span>Tone: {product.emotion_tone}</span>
                  <span>•</span>
                  <span>Calls: {product.analytics?.total_calls || 0}</span>
                  <span>•</span>
                  <span>Conversion: {product.analytics?.conversion_rate?.toFixed(1) || 0}%</span>
                </div>
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => handleSetActive(product._id)}
                  disabled={product.isActive}
                  className={`p-2 rounded-lg ${
                    product.isActive 
                      ? 'bg-gray-100 text-gray-400 cursor-not-allowed' 
                      : 'bg-blue-100 text-blue-600 hover:bg-blue-200'
                  }`}
                >
                  <CheckIcon className="h-4 w-4" />
                </button>
                <button
                  onClick={() => handleEdit(product)}
                  className="p-2 bg-yellow-100 text-yellow-600 hover:bg-yellow-200 rounded-lg"
                >
                  <PencilIcon className="h-4 w-4" />
                </button>
                <button
                  onClick={() => handleDelete(product._id)}
                  className="p-2 bg-red-100 text-red-600 hover:bg-red-200 rounded-lg"
                >
                  <TrashIcon className="h-4 w-4" />
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Product Form Modal */}
      {showForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-4xl max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-semibold">
                {editingProduct ? 'Edit Product' : 'New Product'}
              </h2>
              <button
                onClick={() => {
                  setShowForm(false);
                  setEditingProduct(null);
                  resetForm();
                }}
                className="text-gray-400 hover:text-gray-600"
              >
                <XMarkIcon className="h-6 w-6" />
              </button>
            </div>

            <form onSubmit={handleSubmit} className="space-y-6">
              {/* Basic Information */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Brand Name
                  </label>
                  <input
                    type="text"
                    value={formData.brand_name}
                    onChange={(e) => setFormData(prev => ({ ...prev, brand_name: e.target.value }))}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Product Name
                  </label>
                  <input
                    type="text"
                    value={formData.product_name}
                    onChange={(e) => setFormData(prev => ({ ...prev, product_name: e.target.value }))}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2"
                    required
                  />
                </div>
              </div>

              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Category
                  </label>
                  <select
                    value={formData.category}
                    onChange={(e) => setFormData(prev => ({ ...prev, category: e.target.value }))}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2"
                  >
                    <option value="travel">Travel</option>
                    <option value="food">Food</option>
                    <option value="service">Service</option>
                    <option value="electronics">Electronics</option>
                    <option value="healthcare">Healthcare</option>
                    <option value="education">Education</option>
                    <option value="finance">Finance</option>
                    <option value="other">Other</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Product Type
                  </label>
                  <select
                    value={formData.product_type}
                    onChange={(e) => setFormData(prev => ({ ...prev, product_type: e.target.value }))}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2"
                  >
                    <option value="low">Low Ticket</option>
                    <option value="medium">Medium Ticket</option>
                    <option value="high">High Ticket</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Emotion Tone
                  </label>
                  <select
                    value={formData.emotion_tone}
                    onChange={(e) => setFormData(prev => ({ ...prev, emotion_tone: e.target.value }))}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2"
                  >
                    <option value="friendly">Friendly</option>
                    <option value="trustworthy">Trustworthy</option>
                    <option value="luxury">Luxury</option>
                    <option value="professional">Professional</option>
                    <option value="casual">Casual</option>
                    <option value="urgent">Urgent</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Offer Tagline
                </label>
                <input
                  type="text"
                  value={formData.offer_tagline}
                  onChange={(e) => setFormData(prev => ({ ...prev, offer_tagline: e.target.value }))}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Call to Action
                </label>
                <input
                  type="text"
                  value={formData.call_to_action}
                  onChange={(e) => setFormData(prev => ({ ...prev, call_to_action: e.target.value }))}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2"
                  required
                />
              </div>

              {/* AIDA Stage Content */}
              <div className="space-y-4">
                <h3 className="text-lg font-semibold text-gray-900">AIDA Stage Content</h3>
                
                {/* Attention Hooks */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Attention Hooks
                  </label>
                  <div className="space-y-2">
                    {formData.attention_hooks.map((hook, index) => (
                      <div key={index} className="flex gap-2">
                        <input
                          type="text"
                          value={hook}
                          onChange={(e) => {
                            const newHooks = [...formData.attention_hooks];
                            newHooks[index] = e.target.value;
                            setFormData(prev => ({ ...prev, attention_hooks: newHooks }));
                          }}
                          className="flex-1 border border-gray-300 rounded-lg px-3 py-2"
                        />
                        <button
                          type="button"
                          onClick={() => removeArrayItem('attention_hooks', index)}
                          className="px-3 py-2 bg-red-100 text-red-600 rounded-lg hover:bg-red-200"
                        >
                          <XMarkIcon className="h-4 w-4" />
                        </button>
                      </div>
                    ))}
                    <button
                      type="button"
                      onClick={() => addArrayItem('attention_hooks', '')}
                      className="text-blue-600 hover:text-blue-800 text-sm"
                    >
                      + Add Attention Hook
                    </button>
                  </div>
                </div>

                {/* Interest Questions */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Interest Questions
                  </label>
                  <div className="space-y-2">
                    {formData.interest_questions.map((question, index) => (
                      <div key={index} className="flex gap-2">
                        <input
                          type="text"
                          value={question}
                          onChange={(e) => {
                            const newQuestions = [...formData.interest_questions];
                            newQuestions[index] = e.target.value;
                            setFormData(prev => ({ ...prev, interest_questions: newQuestions }));
                          }}
                          className="flex-1 border border-gray-300 rounded-lg px-3 py-2"
                        />
                        <button
                          type="button"
                          onClick={() => removeArrayItem('interest_questions', index)}
                          className="px-3 py-2 bg-red-100 text-red-600 rounded-lg hover:bg-red-200"
                        >
                          <XMarkIcon className="h-4 w-4" />
                        </button>
                      </div>
                    ))}
                    <button
                      type="button"
                      onClick={() => addArrayItem('interest_questions', '')}
                      className="text-blue-600 hover:text-blue-800 text-sm"
                    >
                      + Add Interest Question
                    </button>
                  </div>
                </div>

                {/* Desire Statements */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Desire Statements
                  </label>
                  <div className="space-y-2">
                    {formData.desire_statements.map((statement, index) => (
                      <div key={index} className="flex gap-2">
                        <input
                          type="text"
                          value={statement}
                          onChange={(e) => {
                            const newStatements = [...formData.desire_statements];
                            newStatements[index] = e.target.value;
                            setFormData(prev => ({ ...prev, desire_statements: newStatements }));
                          }}
                          className="flex-1 border border-gray-300 rounded-lg px-3 py-2"
                        />
                        <button
                          type="button"
                          onClick={() => removeArrayItem('desire_statements', index)}
                          className="px-3 py-2 bg-red-100 text-red-600 rounded-lg hover:bg-red-200"
                        >
                          <XMarkIcon className="h-4 w-4" />
                        </button>
                      </div>
                    ))}
                    <button
                      type="button"
                      onClick={() => addArrayItem('desire_statements', '')}
                      className="text-blue-600 hover:text-blue-800 text-sm"
                    >
                      + Add Desire Statement
                    </button>
                  </div>
                </div>

                {/* Action Prompts */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Action Prompts
                  </label>
                  <div className="space-y-2">
                    {formData.action_prompts.map((prompt, index) => (
                      <div key={index} className="flex gap-2">
                        <input
                          type="text"
                          value={prompt}
                          onChange={(e) => {
                            const newPrompts = [...formData.action_prompts];
                            newPrompts[index] = e.target.value;
                            setFormData(prev => ({ ...prev, action_prompts: newPrompts }));
                          }}
                          className="flex-1 border border-gray-300 rounded-lg px-3 py-2"
                        />
                        <button
                          type="button"
                          onClick={() => removeArrayItem('action_prompts', index)}
                          className="px-3 py-2 bg-red-100 text-red-600 rounded-lg hover:bg-red-200"
                        >
                          <XMarkIcon className="h-4 w-4" />
                        </button>
                      </div>
                    ))}
                    <button
                      type="button"
                      onClick={() => addArrayItem('action_prompts', '')}
                      className="text-blue-600 hover:text-blue-800 text-sm"
                    >
                      + Add Action Prompt
                    </button>
                  </div>
                </div>
              </div>

              {/* Form Actions */}
              <div className="flex justify-end gap-3 pt-4 border-t">
                <button
                  type="button"
                  onClick={() => {
                    setShowForm(false);
                    setEditingProduct(null);
                    resetForm();
                  }}
                  className="px-4 py-2 text-gray-600 hover:text-gray-800"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600"
                >
                  {editingProduct ? 'Update Product' : 'Create Product'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default AidaProductManager;

